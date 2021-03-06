import * as THREE from 'three'
import SelectionHelper from './SelectionHelper'

export default class InteractionHandler {
  constructor(viewer) {
    this.viewer = viewer
    this.preventSelection = false

    this.selectionHelper = new SelectionHelper(this.viewer, {
      sectionBox: this.sectionBox,
      hover: true
    })
    this.selectionMeshMaterial = new THREE.MeshLambertMaterial({
      color: 0x0b55d2,
      emissive: 0x0b55d2,
      side: THREE.DoubleSide,
      wireframe: false,
      transparent: true,
      opacity: 0.3
    })
    this.selectionMeshMaterial.clippingPlanes = this.viewer.sectionBox.planes
    // Fix overlapping faces flickering
    this.selectionMeshMaterial.polygonOffset = true
    this.selectionMeshMaterial.polygonOffsetFactor = -0.1

    // this.hoverMeshMaterial = new THREE.MeshLambertMaterial( { color: 0x507ecc, emissive: 0x507ecc, side: THREE.DoubleSide } )
    this.hoverMeshMaterial = new THREE.MeshLambertMaterial({
      color: 0x507ecc,
      emissive: 0x507ecc,
      side: THREE.DoubleSide,
      wireframe: false,
      transparent: true,
      opacity: 0.3
    })
    this.hoverMeshMaterial.clippingPlanes = this.viewer.sectionBox.planes
    // Fix overlapping faces flickering
    this.hoverMeshMaterial.polygonOffset = true
    this.hoverMeshMaterial.polygonOffsetFactor = -0.1

    this.selectionLineMaterial = new THREE.LineBasicMaterial({ color: 0x0B55D2 })
    this.selectionLineMaterial.clippingPlanes = this.viewer.sectionBox.planes

    this.selectionEdgesMaterial = new THREE.LineBasicMaterial({ color: 0x23F3BD })
    this.selectionEdgesMaterial.clippingPlanes = this.viewer.sectionBox.planes

    this.selectedObjects = new THREE.Group()
    this.viewer.scene.add(this.selectedObjects)
    this.selectedObjects.renderOrder = 1000
    this.selectionBox = new THREE.Group()
    this.viewer.scene.add(this.selectionBox)

    this.overlayMeshMaterial = new THREE.MeshLambertMaterial({
      color: 0x57f7ff,
      side: THREE.DoubleSide,
      wireframe: false,
      transparent: true,
      opacity: 0.7
    })
    this.overlayMeshMaterial.clippingPlanes = this.viewer.sectionBox.planes
    this.overlaidObjects = new THREE.Group()
    this.viewer.scene.add(this.overlaidObjects)
    this.overlaidObjects.renderOrder = 2000

    this.selectedObjectsUserData = []
    this.selectedRawObjects = []

    this.hoveredObjects = new THREE.Group()
    this.viewer.scene.add( this.hoveredObjects )
    this.hoveredObjects.renderOrder = 1000

    this.hoveredObjectsUserData = []

    this.selectionHelper.on( 'object-doubleclicked', this._handleDoubleClick.bind( this ) )
    this.selectionHelper.on( 'object-clicked', this._handleSelect.bind( this ) )
    this.selectionHelper.on( 'hovered', this._handleHover.bind( this ) )

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.viewer.mouseOverRenderer) {
        this.deselectObjects()
      }
    })
  }

  // used to display objects selected by other users
  overlayObjects(ids = []) {
    this.overlaidObjects.clear()

    let all = this.viewer.sceneManager.allObjects
    let subsetToAdd = all.filter((obj) => ids.indexOf(obj.uuid) !== -1)

    for (let obj of subsetToAdd) {
      let selType = obj.type
      switch (selType) {
        case 'Group': {
          let blockObjs = this.getBlockObjectsCloned(obj)
          for (let child of blockObjs) {
            child.material = this.overlayMeshMaterial
            this.overlaidObjects.add(child)
          }
          break
        }
        case 'Mesh':
          this.overlaidObjects.add(
            new THREE.Mesh(obj.geometry, this.overlayMeshMaterial)
          )
          break
        case 'Line':
          this.overlaidObjects.add(
            new THREE.Line(obj.geometry, this.overlayMeshMaterial)
          )
          break
      }
    }
    this.viewer.needsRender = true
  }

  _handleDoubleClick(objs) {
    if (!objs || objs.length === 0) {
      if (this.viewer.sectionBox.display.visible) {
        this.zoomToObject(this.viewer.sectionBox.cube)
      } else {
        this.zoomExtents()
      }
    } else this.zoomToObject(objs[0].object)
    this.viewer.needsRender = true
    this.viewer.emit(
      'object-doubleclicked',
      objs && objs.length !== 0 ? objs[0].object : null,
      objs && objs.length !== 0 ? objs[0].point : null
    )
  }

  _handleSelect(objs) {
    if (this.viewer.cameraHandler.orbiting) return
    if (this.preventSelection) return

    if (objs.length === 0) {
      this.deselectObjects()
      return
    }

    if (!this.selectionHelper.multiSelect) this.deselectObjects()

    let selType = objs[0].object.type
    let rootBlock = null
    if (
      objs[0].object.parent?.userData?.speckle_type
        ?.toLowerCase()
        .includes('blockinstance')
    ) {
      selType = 'Block'
      rootBlock = this.getParentBlock(objs[0].object.parent)
    }

    let objId = selType === 'Block' ? rootBlock.userData.id : objs[0].object.userData.id
    let objIdIndexCheck = this.selectedObjectsUserData.findIndex((o) => o.id === objId)
    if (objIdIndexCheck !== -1) {
      if (this.selectionHelper.multiSelect) {
        // TODO: deselect if in multiple selection mode
        this.selectedObjectsUserData.splice(objIdIndexCheck, 1)
        this.deselectObj(rootBlock ? rootBlock.userData.id : objs[0].object.userData.id)
      }
      return
    }

    switch (selType) {
      case 'Block': {
        let blockObjs = this.getBlockObjectsCloned(rootBlock)
        for (let child of blockObjs) {
          child.userData = { id: rootBlock.userData.id }
          child.material = this.selectionMeshMaterial
          this.selectedObjects.add(child)
          //this.viewer.outlinePass.selectedObjects.push( child )
        }
        break
      }
      case 'Mesh': {
        let m = new THREE.Mesh(objs[0].object.geometry, this.selectionMeshMaterial)
        m.userData = { id: objs[0].object.userData.id }
        this.selectedObjects.add(m)
        //this.viewer.outlinePass.selectedObjects.push( new THREE.Mesh( objs[0].object.geometry, this.selectionMeshMaterial ) )
        break
      }
      case 'Line': {
        this.selectedObjects.add( new THREE.Line( objs[0].object.geometry, this.selectionLineMaterial ) )
        break
      }
      case 'Point':
        console.warn('Point selection not implemented.')
        return // exit the whole func here, points cause all sorts of trouble when being selected (ie, bbox stuff)
    }

    this.setOrbitPoint(objs[0].object)
    // dehover objects after click event
    this.dehoverObjects()

    if (selType === 'Block') {
      this.selectedObjectsUserData.push(rootBlock.userData)
      this.selectedRawObjects.push(rootBlock)
    } else {
      this.selectedObjectsUserData.push(objs[0].object.userData)
      this.selectedRawObjects.push(objs[0])
    }

    let box = new THREE.Box3().setFromObject(this.selectedObjects)
    let boxHelper = new THREE.Box3Helper(box, 0x047efb)
    this.selectionBox.clear()
    this.selectionBox.add(boxHelper)
    this.viewer.needsRender = true

    let selectionCenter = new THREE.Vector3()
    box.getCenter(selectionCenter)
    let selectionInfo = {
      object: objs[0],
      userData: this.selectedObjectsUserData,
      location: objs[0].point,
      selectionCenter: selectionCenter
    }
    this.viewer.emit('select', selectionInfo)
  }

  _handleHover( objs ) {
    if( this.viewer.cameraHandler.orbiting ) return
    if( this.preventSelection ) return

    if ( objs.length === 0 ) {
      this.dehoverObjects()
      return
    }

    if ( !this.selectionHelper.multiSelect ) this.dehoverObjects()

    // if the hovered item is clicked, don't do anything
    if (this.selectedObjectsUserData.some(e => e.id === objs[0].object.userData.id)) {
      return
    }
    
    let selType = objs[0].object.type
    let rootBlock = null
    if ( objs[0].object.parent?.userData?.speckle_type?.toLowerCase().includes( 'blockinstance' ) ) {
      selType = 'Block'
      rootBlock = this.getParentBlock( objs[0].object.parent )
    }

    switch ( selType ) {
      case 'Block': {
        let blockObjs = this.getBlockObjectsCloned( rootBlock )
        for( let child of blockObjs ) {          
          child.material = this.hoverMeshMaterial
          this.hoveredObjects.add( child )
        }
        break
      }
      case 'Mesh':
        if (objs[0].object.userData.speckle_type == 'SpeckMesh') {
          this.viewer.sphereInter.geometry.parameters['radius'] = 1
          this.viewer.sphereInter.geometry.needsUpdate = true
          const position = objs[0].object.geometry.getAttribute('position')
          const face = objs[0].face;
          const points = [new THREE.Vector3().fromBufferAttribute(position, face.a), new THREE.Vector3().fromBufferAttribute(position, face.b), new THREE.Vector3().fromBufferAttribute(position, face.c)]
          const distances = [objs[0].point.distanceToSquared(points[0]), objs[0].point.distanceToSquared(points[1]), objs[0].point.distanceToSquared(points[2])]
          const min = Math.min(...distances)

          this.viewer.sphereInter.geometry.dispose()
          this.viewer.sphereInter.geometry = new THREE.SphereGeometry( 1 / 210 * objs[0].distance + 1 / 14);
          this.viewer.sphereInter.position.copy( points[distances.indexOf(min)] );
          this.viewer.sphereInter.visible = true
        }
        else this.viewer.sphereInter.visible = false
        this.hoveredObjects.add( new THREE.Mesh( objs[0].object.geometry, this.hoverMeshMaterial ) )
        break
      case 'Line':
        this.hoveredObjects.add( new THREE.Line( objs[0].object.geometry, this.hoverMeshMaterial ) )
        break
      case 'Point':
        console.warn( 'Point selection not implemented.' )
        return // exit the whole func here, points cause all sorts of trouble when being selected (ie, bbox stuff)
    }

    let box 
    if ( selType === 'Block' ) {
      this.hoveredObjectsUserData.push( rootBlock.userData )
      box = new THREE.BoxHelper( rootBlock, 0x23F3BD )
    } else {
      this.hoveredObjectsUserData.push( objs[0].object.userData )
      box = new THREE.BoxHelper( objs[0].object, 0x23F3BD )
    }
    
    box.material = this.selectionEdgesMaterial
    this.hoveredObjects.add( box )
    this.viewer.needsRender = true
    this.viewer.emit( 'hover', this.hoveredObjectsUserData )
  }

  // function to have the camera rotate around a member when it is selected like in Revit
  setOrbitPoint( target ) {
    var _v3A = new THREE.Vector3();
    var _xColumn = new THREE.Vector3();
    var _yColumn = new THREE.Vector3();
    var _zColumn = new THREE.Vector3();

    const box = new THREE.Box3().setFromObject( target )
    if( box.max.x === Infinity || box.max.x === -Infinity ) {
      box = new THREE.Box3( new THREE.Vector3( -1,-1,-1 ), new THREE.Vector3( 1,1,1 ) )
    }

    _xColumn.setFromMatrixColumn( this.viewer.cameraHandler.activeCam.camera.matrixWorldInverse, 0 );
    _yColumn.setFromMatrixColumn( this.viewer.cameraHandler.activeCam.camera.matrixWorldInverse, 1 );
    _zColumn.setFromMatrixColumn( this.viewer.cameraHandler.activeCam.camera.matrixWorldInverse, 2 );

    const targetX = (box.max.x + box.min.x) / 2;
    const targetY = (box.max.y + box.min.y) / 2;
    const targetZ = (box.max.z + box.min.z) / 2;

    const position = _v3A.set( targetX, targetY, targetZ );
    const distance = position.distanceTo( this.viewer.cameraHandler.activeCam.camera.position );
    const cameraToPoint = position.sub( this.viewer.cameraHandler.activeCam.camera.position );
    _xColumn.multiplyScalar( cameraToPoint.x );
    _yColumn.multiplyScalar( cameraToPoint.y );
    _zColumn.multiplyScalar( cameraToPoint.z );

    _v3A.copy( _xColumn ).add( _yColumn ).add( _zColumn );
    _v3A.z = _v3A.z + distance;

    this.viewer.cameraHandler.controls.dollyTo( distance, false );
    this.viewer.cameraHandler.controls.setFocalOffset( - _v3A.x, _v3A.y, - _v3A.z, false );
    this.viewer.cameraHandler.controls.moveTo( targetX, targetY, targetZ, false );
  }

  getParentBlock( block ) {
    if( block.parent?.userData?.speckle_type?.toLowerCase().includes( 'blockinstance' ) ) {
      return this.getParentBlock( block.parent )
    }
    this.viewer.emit('select', selectionInfo)
  }

  getParentBlock(block) {
    if (block.parent?.userData?.speckle_type?.toLowerCase().includes('blockinstance')) {
      return this.getParentBlock(block.parent)
    } else return block
  }

  getBlockObjectsCloned(block, objects = []) {
    for (let child of block.children) {
      if (child instanceof THREE.Group) {
        objects.push(...this.getBlockObjectsCloned(child))
      } else {
        objects.push(child.clone())
      }
    }
    for (let child of objects) {
      child.geometry = child.geometry.clone().applyMatrix4(block.matrix)
    }
    return objects
  }

  deselectObj(id) {
    let objToRemove = this.selectedObjects.children.filter((o) => o.userData.id === id)
    for (const o of objToRemove) this.selectedObjects.remove(o)

    this.selectionBox.clear()
    if (this.selectedObjects.children.length !== 0) {
      let box = new THREE.Box3().setFromObject(this.selectedObjects)
      let boxHelper = new THREE.Box3Helper(box, 0x047efb)
      this.selectionBox.add(boxHelper)
    }
    this.viewer.needsRender = true
  }

  deselectObjects() {
    this.selectedObjects.clear()
    this.selectionBox.clear()
    this.selectedObjectsUserData = []
    this.selectedRawObjects = []
    this.viewer.needsRender = true
    this.viewer.emit('select', { userData: [], location: null })
  }

  dehoverObjects() {
    this.viewer.sphereInter.visible = false
    this.hoveredObjects.clear()
    this.hoveredObjectsUserData = []
    this.viewer.needsRender = true
    this.viewer.emit( 'hover', this.hoveredObjectsUserData )
  }

  zoomToObjectId( id ) {
    let obj = this.viewer.sceneManager.allObjects.find( o => o.uuid === id )
    if( obj ) this.zoomToObject( obj )
    else console.warn( `No object with id of ${id} found.` )
  }

  zoomToObject(target, fit = 1.2, transition = true) {
    const box = new THREE.Box3().setFromObject(target)
    this.zoomToBox(box, fit, transition)
  }

  zoomExtents(fit = 1.2, transition = true) {
    if (this.viewer.sectionBox.display.visible) {
      this.zoomToObject(this.viewer.sectionBox.cube)
      return
    }
    if (this.viewer.sceneManager.sceneObjects.objectsInScene.length === 0) {
      let box = new THREE.Box3(
        new THREE.Vector3(-1, -1, -1),
        new THREE.Vector3(1, 1, 1)
      )
      this.zoomToBox(box, fit, transition)
      return
    }

    let box = new THREE.Box3().setFromObject(
      this.viewer.sceneManager.sceneObjects.objectsInScene
    )
    this.zoomToBox(box, fit, transition)
    // this.viewer.controls.setBoundary( box )
  }

  zoomToBox(box, fit = 1.2, transition = true) {
    if (box.max.x === Infinity || box.max.x === -Infinity) {
      box = new THREE.Box3(new THREE.Vector3(-1, -1, -1), new THREE.Vector3(1, 1, 1))
    }
    const fitOffset = fit

    const size = box.getSize(new THREE.Vector3())
    let target = new THREE.Sphere()
    box.getBoundingSphere(target)
    target.radius = target.radius * fitOffset

    const maxSize = Math.max(size.x, size.y, size.z)
    const camFov = this.viewer.cameraHandler.camera.fov
      ? this.viewer.cameraHandler.camera.fov
      : 55
    const camAspect = this.viewer.cameraHandler.camera.aspect
      ? this.viewer.cameraHandler.camera.aspect
      : 1.2
    const fitHeightDistance = maxSize / (2 * Math.atan((Math.PI * camFov) / 360))
    const fitWidthDistance = fitHeightDistance / camAspect
    const distance = fitOffset * Math.max(fitHeightDistance, fitWidthDistance)

    this.viewer.cameraHandler.controls.fitToSphere(target, transition)

    this.viewer.cameraHandler.controls.minDistance = distance / 100
    this.viewer.cameraHandler.controls.maxDistance = distance * 100
    this.viewer.cameraHandler.camera.near = distance / 100
    this.viewer.cameraHandler.camera.far = distance * 100
    this.viewer.cameraHandler.camera.updateProjectionMatrix()

    if (this.viewer.cameraHandler.activeCam.name === 'ortho') {
      this.viewer.cameraHandler.orthoCamera.far = distance * 100
      this.viewer.cameraHandler.orthoCamera.updateProjectionMatrix()

      // fit the camera inside, so we don't have clipping plane issues.
      // WIP implementation
      let camPos = this.viewer.cameraHandler.orthoCamera.position
      let dist = target.distanceToPoint(camPos)
      if (dist < 0) {
        dist *= -1
        this.viewer.cameraHandler.controls.setPosition(
          camPos.x + dist,
          camPos.y + dist,
          camPos.z + dist
        )
      }
    }
  }

  rotateCamera(azimuthAngle = 0.261799, polarAngle = 0, transition = true) {
    this.viewer.cameraHandler.controls.rotate(azimuthAngle, polarAngle, transition)
  }

  screenshot() {
    let sectionBoxVisible = this.viewer.sectionBox.display.visible
    if (sectionBoxVisible) {
      this.viewer.sectionBox.displayOff()
      this.viewer.needsRender = true
      this.viewer.render()
    }
    const screenshot = this.viewer.renderer.domElement.toDataURL('image/png')
    if (sectionBoxVisible) {
      this.viewer.sectionBox.displayOn()
    }
    return screenshot
  }

  /**
   * Rotates camera to some canonical views
   * @param  {string}  side       Can be any of front, back, up (top), down (bottom), right, left.
   * @param  {Number}  fit        [description]
   * @param  {Boolean} transition [description]
   * @return {[type]}             [description]
   */
  rotateTo(side, transition = true) {
    const DEG90 = Math.PI * 0.5
    const DEG180 = Math.PI

    switch (side) {
      case 'front':
        this.viewer.cameraHandler.controls.rotateTo(0, DEG90, transition)
        if (this.viewer.cameraHandler.activeCam.name === 'ortho')
          this.viewer.cameraHandler.disableRotations()
        break

      case 'back':
        this.viewer.cameraHandler.controls.rotateTo(DEG180, DEG90, transition)
        if (this.viewer.cameraHandler.activeCam.name === 'ortho')
          this.viewer.cameraHandler.disableRotations()
        break

      case 'up':
      case 'top':
        this.viewer.cameraHandler.controls.rotateTo(0, 0, transition)
        if (this.viewer.cameraHandler.activeCam.name === 'ortho')
          this.viewer.cameraHandler.disableRotations()
        break

      case 'down':
      case 'bottom':
        this.viewer.cameraHandler.controls.rotateTo(0, DEG180, transition)
        if (this.viewer.cameraHandler.activeCam.name === 'ortho')
          this.viewer.cameraHandler.disableRotations()
        break

      case 'right':
        this.viewer.cameraHandler.controls.rotateTo(DEG90, DEG90, transition)
        if (this.viewer.cameraHandler.activeCam.name === 'ortho')
          this.viewer.cameraHandler.disableRotations()
        break

      case 'left':
        this.viewer.cameraHandler.controls.rotateTo(-DEG90, DEG90, transition)
        if (this.viewer.cameraHandler.activeCam.name === 'ortho')
          this.viewer.cameraHandler.disableRotations()
        break

      case '3d':
      case '3D':
      default: {
        let box
        if (this.viewer.sceneManager.sceneObjects.allObjects.children.length === 0)
          box = new THREE.Box3(
            new THREE.Vector3(-1, -1, -1),
            new THREE.Vector3(1, 1, 1)
          )
        else
          box = new THREE.Box3().setFromObject(
            this.viewer.sceneManager.sceneObjects.allObjects
          )
        if (box.max.x === Infinity || box.max.x === -Infinity) {
          box = new THREE.Box3(
            new THREE.Vector3(-1, -1, -1),
            new THREE.Vector3(1, 1, 1)
          )
        }
        this.viewer.cameraHandler.controls.setPosition(
          box.max.x,
          box.max.y,
          box.max.z,
          transition
        )
        this.zoomExtents()
        this.viewer.cameraHandler.enableRotations()
        break
      }
    }
  }

  getViews() {
    return this.viewer.sceneManager.views.map((v) => {
      return { name: v.applicationId, id: v.id, view: v }
    })
  }

  setView(id, transition = true) {
    if (!id) return
    let view = this.viewer.sceneManager.views.find((v) => v.id === id)
    if (!view) {
      console.warn(`View id ${id} not found.`)
      return
    }

    let target = view.target
    let position = view.origin

    this.viewer.cameraHandler.activeCam.controls.setLookAt(
      position.x,
      position.y,
      position.z,
      target.x,
      target.y,
      target.z,
      transition
    )
  }

  setLookAt(position, target, transition = true) {
    if (!position || !target) return
    this.viewer.cameraHandler.activeCam.controls.setLookAt(
      position.x,
      position.y,
      position.z,
      target.x,
      target.y,
      target.z,
      transition
    )
  }
}

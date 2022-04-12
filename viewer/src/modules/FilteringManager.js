import * as THREE from 'three'
import Rainbow from 'rainbowvis.js'

export default class FilteringManager {
  constructor(viewer) {
    this.viewer = viewer
    this.WireframeMaterial = new THREE.MeshStandardMaterial({
      color: 0x7080a0,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.2,
      wireframe: false
    })
    // console.log(this.viewer.sectionBox.planes)

    this.ColoredMaterial = new THREE.MeshStandardMaterial({
      color: 0x7080a0,
      side: THREE.DoubleSide,
      transparent: false,
      clippingPlanes: this.viewer.sectionBox.planes
    })

    this.colorLegend = {}
  }

  filterAndColorObject(obj, filter) {
    if (!filter) return obj.clone()

    if (!this.passesFilter(obj.userData, filter.filterBy)) {
      if (filter.ghostOthers) {
        let clone = obj.clone()
        this.ghostObject(clone)
        return clone
      }
      return null
    }

    let clone = obj.clone()
    if (filter.wireframe !== 'undefined') { 
      this.toggleWireframe(obj, filter.wireframe)
      obj.material.needsUpdate = true
      clone = obj.clone()
    }
    if (filter.showDeformed) { 
      clone.geometry = clone.geometry.clone()
      clone.material = clone.material.clone()
      this.deformFloorsByVertices(clone, filter.showDeformed)
      clone.geometry.computeBoundingBox();
      clone.geometry.computeBoundingSphere();
    }
    if (filter.colorBy) {
      if (filter.colorBy.type === 'category') {
        let newMaterial = this.colorWithCategory(obj, filter.colorBy)
        this.setMaterial(clone, newMaterial)
      } else if (filter.colorBy.type === 'gradient') {
        let newMaterial = this.colorWithGradient(obj, filter.colorBy)
        this.setMaterial(clone, newMaterial)
      } else if (filter.colorBy.type === 'FEM') {
        this.colorFloorsByVertices(obj, filter.colorBy)
        clone = obj.clone()
      }
    }
    console.log('CLONE WIREMESH', clone.material.wireframe)
    return clone
  }

  filterAndColorMeshObject(filter) {
    var meshes = this.getObjsInGroupThatPassFilter(this.viewer.sceneManager.sceneObjects.allSolidObjects, filter)
    console.log(meshes)
    for (var mesh of meshes) {
      console.log(mesh)
      if (filter.wireframe !== 'undefined') { 
        console.log('toggleWireframe')
        if (filter.wireframe === true) mesh.material.wireframe = true;
        else if (filter.wireframe === false) mesh.material.wireframe = false;
      }
      // mesh.material.needsUpdate = true;
      this.viewer.needsRender = true
    }
  }

  ghostObject(clone) {
    clone.userData = { hidden: true }

    if (clone.type === 'Group') {
      for (let child of clone.children) {
        this.ghostObject(child)
      }
    } else if (clone.type === 'Mesh') {
      clone.material = clone.material.clone()
      clone.material.clippingPlanes = null
      clone.material.transparent = true
      clone.material.opacity = 0.05
    } else {
      clone.visible = false
    }
  }

  setMaterial(clone, material) {
    if (clone.type === 'Group') {
      for (let child of clone.children) {
        this.setMaterial(child, material)
      }
    } else if (clone.material !== undefined && material !== undefined) {
      clone.material = material
      clone.material.clippingPlanes = this.viewer.sectionBox.planes
    }
  }

  getObjectProperty(obj, property) {
    if (!property) return
    let keyParts = property.split('.')
    let crtObj = obj
    for (let i = 0; i < keyParts.length - 1; i++) {
      if (!(keyParts[i] in crtObj)) return
      crtObj = crtObj[keyParts[i]]
      if (crtObj.constructor !== Object) return
    }
    let attributeName = keyParts[keyParts.length - 1]
    return crtObj[attributeName]
  }

  getObjsInGroupThatPassFilter(group, filter) {
    var objsToReturn = []
    for ( let obj of group.children ) {
      var passes = this.passesFilter(obj.userData, filter.filterBy)
      if (passes) {
        objsToReturn.push(obj)
      }
    }
    return objsToReturn
  }
  
  colorWithCategory( threejsObj, colors ) {
    let obj = threejsObj.userData
    let defaultValue = colors.default
    let color = defaultValue
    let objValue = this.getObjectProperty(obj, colors.property)
    let customPallete = colors.values || {}
    if (objValue in customPallete) {
      color = customPallete[objValue]
    }

    if (color === null) {
      return threejsObj.material
    } else if (color === undefined) {
      // compute value hash
      let objValueAsString = '' + objValue
      let hash = 0
      for (let i = 0; i < objValueAsString.length; i++) {
        let chr = objValueAsString.charCodeAt(i)
        hash = (hash << 5) - hash + chr
        hash |= 0 // Convert to 32bit integer
      }
      hash = Math.abs(hash)
      let colorHue = hash % 360
      color = `hsl(${colorHue}, 50%, 30%)`
    }

    if (objValue !== undefined && objValue !== null)
      this.colorLegend[objValue.toString()] = color

    let material = this.ColoredMaterial.clone()
    material.color = new THREE.Color(color)
    return material
  }

  colorWithGradient(threejsObj, colors) {
    let obj = threejsObj.userData
    let rainbow = new Rainbow()
    if ('minValue' in colors && 'maxValue' in colors)
      rainbow.setNumberRange(colors.minValue, colors.maxValue)
    if ('gradientColors' in colors) rainbow.setSpectrum(...colors.gradientColors)

    let objValue = this.getObjectProperty(obj, colors.property)
    objValue = Number(objValue)
    if (Number.isNaN(objValue)) {
      let defaultColor = colors.default
      if (defaultColor === null) return threejsObj.material
      if (defaultColor === undefined) return this.WireframeMaterial

      let material = this.ColoredMaterial.clone()
      material.color = new THREE.Color(defaultColor)
      return material
    }

    let material = this.ColoredMaterial.clone()
    material.color = new THREE.Color(`#${rainbow.colourAt(objValue)}`)
    return material
  }

  toggleWireframe(floorObj, wireframe) {
    if (wireframe === true) floorObj.material.wireframe = true;
    else if (wireframe === false) floorObj.material.wireframe = false;
  }

  // toggleWireframe(floorObj, wireframe) {
  //   if (wireframe === true) {
  //     if (!floorObj.geometry.getAttribute('color')) {
  //       console.log('wireframe no color')
  //       floorObj.material = this.viewer.sceneManager.femMeshMaterial.clone()
  //     }
  //     floorObj.material.wireframe = true;
  //   } else if (wireframe === false) {
  //     if (!floorObj.geometry.getAttribute('color')) floorObj.material = this.viewer.sceneManager.solidMaterial.clone()
  //     floorObj.material.wireframe = false;
  //   }
  //   return floorObj.material
  // }

  colorFloorsByVertices(floorObj, colors) {
    let rainbow = new Rainbow()
    if (!floorObj.userData.cell_data) return floorObj.material

    console.log(floorObj.material.wireframe)
    const wireframe = floorObj.material.wireframe
    if(!colors.property) {
      floorObj.geometry.deleteAttribute('color')
      if (wireframe) {
      } else {
        floorObj.material = this.viewer.sceneManager.solidMaterial.clone()
      }
      return
    } else {
      floorObj.material = this.viewer.sceneManager.femMeshMaterial.clone()
      floorObj.material.wireframe = wireframe
    }

    let objValue = this.getObjectProperty(floorObj.userData.cell_data, colors.property)
    if (typeof(floorObj.geometry.getAttribute('color')) === "undefined") {
      console.log(floorObj)
      floorObj.geometry.setAttribute(
        'color',
        new THREE.BufferAttribute(
          new Float32Array(floorObj.geometry.getAttribute('position').count * 3),
          3
        )
      )
    }

    var minVal = Infinity;
    var maxVal = -Infinity;
    let val;

    let dir;
    try {
      dir = parseInt(colors.direction)
    } catch {
      dir = 2
    }

    if (dir == 0 || dir == 1) {
      for (var i = 0; i < objValue.length; i++) {
        val = objValue[i][dir]
        minVal = Math.min(minVal, val)
        maxVal = Math.max(maxVal, val)
      }
      rainbow.setNumberRange(minVal, maxVal)
      rainbow.setSpectrum(...['blue', 'gray', 'red'])
      for (var i = 0; i < objValue.length; i++) {
        let color = new THREE.Color(`#${rainbow.colourAt(objValue[i][dir])}`)
        floorObj.geometry.attributes.color.setXYZ(i, color.r, color.g, color.b)
      }
    } else {
      for (var i = 0; i < objValue.length; i++) {
        val = Math.sqrt(objValue[i][0] ** 2 + objValue[i][1] ** 2)
        minVal = Math.min(minVal, val)
        maxVal = Math.max(maxVal, val)
      }
      rainbow.setNumberRange(minVal, maxVal)
      rainbow.setSpectrum(...['blue', 'gray', 'red'])
      for (var i = 0; i < objValue.length; i++) {
        let color = new THREE.Color(`#${rainbow.colourAt(Math.sqrt(objValue[i][0] ** 2 + objValue[i][1] ** 2))}`)
        floorObj.geometry.attributes.color.setXYZ(i, color.r, color.g, color.b)
      }
    }
    return floorObj.material
  }

  deformFloorsByVertices(floorObj, multiplier) {
    let displacements = this.getObjectProperty(floorObj.userData.cell_data, 'displacements')
    for (var i = 0; i < displacements.length; i++) {
      floorObj.geometry.getAttribute('position').setXYZ(i, floorObj.geometry.getAttribute('position').array[i*3] + displacements[i][0]*multiplier, floorObj.geometry.getAttribute('position').array[i*3+1] + displacements[i][1]*multiplier, floorObj.geometry.getAttribute('position').array[i*3+2])
    }
  }

  passesFilter(obj, filterBy) {
    if (!filterBy) return true
    for (let filterKey in filterBy) {
      let objValue = this.getObjectProperty(obj, filterKey)

      let passesFilter = this.filterValue(objValue, filterBy[filterKey])
      if (!passesFilter) return false
    }
    return true
  }

  filterValue(objValue, valueFilter) {
    // Array value filter means it can be any value from the array
    if (Array.isArray(valueFilter)) return valueFilter.includes(objValue)

    // Dictionary value filter can specify ranges with `lte` and `gte` fields (LowerThanOrEqual, GreaterThanOrEqual)
    if (valueFilter.constructor === Object) {
      if ('not' in valueFilter && Array.isArray(valueFilter.not)) {
        if (valueFilter.not.includes(objValue)) return false
      }

      if ('includes' in valueFilter && Array.isArray(valueFilter.includes)) {
        if (!objValue || !Array.isArray(objValue)) return false
        for (let testValue of valueFilter.includes)
          if (objValue.includes(testValue)) return true
        return false
      }

      if ('excludes' in valueFilter && Array.isArray(valueFilter.excludes)) {
        if (!objValue || !Array.isArray(objValue)) return true
        for (let testValue of valueFilter.excludes)
          if (objValue.includes(testValue)) return false
        return true
      }

      if ('lte' in valueFilter && !(objValue <= valueFilter.lte)) return false
      if ('gte' in valueFilter && !(objValue >= valueFilter.gte)) return false
      return true
    }

    // Can also filter by specific value
    return objValue === valueFilter
  }

  initFilterOperation() {
    this.colorLegend = {}
  }
}

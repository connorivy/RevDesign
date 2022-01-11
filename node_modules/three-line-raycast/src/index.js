import * as THREE from 'three'
var inverseMatrix = new THREE.Matrix4()
var ray = new THREE.Ray()
var sphere = new THREE.Sphere()
var interRay = new THREE.Vector3()
export function LineRaycast(raycaster, intersects) {
  var geometry = this.geometry
  // Checking boundingSphere distance to ray
  if (!geometry.boundingSphere) geometry.computeBoundingSphere()
  sphere.copy(geometry.boundingSphere)
  sphere.applyMatrix4(this.matrixWorld)

  if (raycaster.ray.intersectSphere(sphere, interRay) === false) {
    return
  }

  inverseMatrix.getInverse(this.matrixWorld)
  ray.copy(raycaster.ray).applyMatrix4(inverseMatrix)

  var startPoints = geometry.attributes.instanceStart
  var endPoints = geometry.attributes.instanceEnd
  var vStart = new THREE.Vector3()
  var vEnd = new THREE.Vector3()
  var interSegment = new THREE.Vector3()

  for (var i = 0, l = startPoints.count; i < l; i += 1) {
    vStart.set(startPoints.getX(i), startPoints.getY(i), startPoints.getZ(i))
    vEnd.set(endPoints.getX(i), endPoints.getY(i), endPoints.getZ(i))
    var precision = raycaster.linePrecision + this.material.linewidth / 2
    var precisionSq = precision * precision

    var distSq = ray.distanceSqToSegment(vStart, vEnd, interRay, interSegment)

    if (distSq > precisionSq) continue

    interRay.applyMatrix4(this.matrixWorld) //Move back to world space for distance calculation

    var distance = raycaster.ray.origin.distanceTo(interRay)

    if (distance < raycaster.near || distance > raycaster.far) continue

    intersects.push({
      distance: distance,
      // What do we want? intersection point on the ray or on the segment??
      // point: raycaster.ray.at( distance ),
      point: interSegment.clone().applyMatrix4(this.matrixWorld),
      index: i,
      face: null,
      faceIndex: null,
      object: this,
    })
    // make event only fire once
    i = l
  }
}

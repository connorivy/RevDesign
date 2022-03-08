 /* eslint-disable */
import Viewer from '../../viewer/src/modules/Viewer'

setInterval(() => {
  document.getElementById('info-mem').innerText = '' + Math.round(performance.memory.usedJSHeapSize / 1024 / 1024)
}, 100 )

let v = new Viewer( { container: document.getElementById( 'threejs-container' ), showStats: true } )
v.on( 'load-progress', args => {
  document.getElementById('info-progress').innerText = `${Math.round(1000 * args.progress) / 1000 }`
} )

v.on( 'busy', isBusy => {
  document.getElementById('info-busy').innerText = isBusy ? 'BUSY' : 'idle'
  document.body.style.cursor = isBusy ? 'progress' : 'default'
} )

window.v = v
window.addEventListener( 'load', () => {
  v.onWindowResize()
  const prevLoadUrl = localStorage.getItem( 'prevLoadUrl' )
  console.log( prevLoadUrl )
  if (prevLoadUrl) document.getElementById('objectUrlInput').value = prevLoadUrl;
} )

window.loadData = async function LoadData( url ) {
  // url = 'https://speckle.xyz/streams/2413489097/objects/4995b1c402ec5c0ce60d2ca0b9d443f8'  // jesuit
  // url = 'https://speckle.xyz/streams/9250125033/objects/6fa3832f10f42f4b46a7acd66fe5e3d5' // toll brothers floors and shear walls
  // url = 'https://speckle.xyz/streams/218b84525a/objects/d63d1dc2da9f28f6c6601f45188bcc76' // test floor from notes on date 3-19
  url = url || document.getElementById( 'objectUrlInput' ).value
  localStorage.setItem( 'prevLoadUrl', url )
  let t0 = Date.now()
  await v.loadObject( url )
  console.log(`Finished loading in: ${(Date.now() - t0) / 1000}`)
} 

loadData()

v.on( 'select', objects => {
  console.info( `Selection event. Current selection count: ${objects.length}.` )
  console.log( objects )
} )

v.on( 'object-doubleclicked', obj => {
  console.info( 'Object double click event.' )
  console.log( obj ? obj : 'nothing was doubleckicked.' )
} )

v.on( 'section-box', status => {
  console.info( `Section box is now ${status ? 'on' : 'off'}.` )
} )

window.viewerScreenshot = function() {
  let data = v.interactions.screenshot() // transparent png.

  let pop = window.open()
  pop.document.title = 'super screenshot'
  pop.document.body.style.backgroundColor = 'grey'

  let img = new Image()
  img.src = data
  pop.document.body.appendChild( img )
}

window.zoomFast = function(){
  v.interactions.zoomExtents( 0.95, false )
}


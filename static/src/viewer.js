 /* eslint-disable */
import Viewer from '../../viewer/src/modules/Viewer'

// setInterval(() => {
//   document.getElementById('info-mem').innerText = '' + Math.round(performance.memory.usedJSHeapSize / 1024 / 1024)
// }, 100 )

let v = new Viewer( { container: document.getElementById( 'threejs-container' ), showStats: false } )
// v.on( 'load-progress', args => {
//   document.getElementById('info-progress').innerText = `${Math.round(1000 * args.progress) / 1000 }`
// } )

// v.on( 'busy', isBusy => {
//   document.getElementById('info-busy').innerText = isBusy ? 'BUSY' : 'idle'
//   document.body.style.cursor = isBusy ? 'progress' : 'default'
// } )

window.v = v
window.addEventListener( 'load', () => {
  v.onWindowResize()
  const prevLoadUrl = localStorage.getItem( 'prevLoadUrl' )
  console.log( prevLoadUrl )
  let segments = prevLoadUrl.split( '/' )

  if ( segments.length < 7 ) {
    throw new Error( 'Unexpected object url format.' )
  }

  if (prevLoadUrl) document.getElementById('objectUrlInput').value = segments[4];
} )

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


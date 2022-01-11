# three-line-raycast
Raycast function for three.js `Line2` that accounts for line width

    npm install three-line-raycast

# How to use

#### Import Line2 & LineRaycast

```js
import { Line2 } from "three/examples/jsm/lines/Line2.js";
import { LineRaycast } from 'three-line-raycast'
```

#### Create Line2 and add LineRaycast

First create a Line2 Mesh, then add the LineRaycast function.

Details on Line2 can be found at the [three.js example](https://threejs.org/examples/?q=line#webgl_lines_fat)

```js
line = new Line2( geometry, matLine );
line.raycast = LineRaycast;
```

#### That's it! Now you can use the raycast on lines!
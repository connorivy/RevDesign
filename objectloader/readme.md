# The Speckle Object Loader

[![Twitter Follow](https://img.shields.io/twitter/follow/SpeckleSystems?style=social)](https://twitter.com/SpeckleSystems) [![Community forum users](https://img.shields.io/discourse/users?server=https%3A%2F%2Fspeckle.community&style=flat-square&logo=discourse&logoColor=white)](https://speckle.community) [![website](https://img.shields.io/badge/https://-speckle.systems-royalblue?style=flat-square)](https://speckle.systems) [![docs](https://img.shields.io/badge/docs-speckle.guide-orange?style=flat-square&logo=read-the-docs&logoColor=white)](https://speckle.guide/dev/) [![npm version](https://badge.fury.io/js/%40speckle%2Fobjectloader.svg)](https://badge.fury.io/js/%40speckle%2Fobjectloader)

## Documentation

Comprehensive developer and user documentation can be found in our:

#### 📚 [Speckle Docs website](https://speckle.guide/dev/)

## Getting started

This is a small utility class that helps you stream an object and all its sub-components from the Speckle Server API. It is intended to be used in contexts where you want to "download" the whole object, or iteratively traverse its whole tree.

Here's a sample way on how to use it, pfilfered from the [3d viewer package](../viewer):

```js


async load( { serverUrl, token, streamId, objectId } ) {

  const loader = new ObjectLoader( { serverUrl, token, streamId, objectId } )

  let total = null
  let count = 0

  for await ( let obj of loader.getObjectIterator() ) {

    if( !total ) total = obj.totalChildrenCount

    console.log( obj, `Progress: ${count++}/${total}` )

  }

}

```

If you do not want to process the objects one by one as they are streamed to you, you can use the `getAndConstructObject()` method. Here's an example: 

```js

let loader = new ObjectLoader( {
  serverUrl: "https://latest.speckle.dev", 
  streamId: "3ed8357f29", 
  objectId: "0408ab9caaa2ebefb2dd7f1f671e7555",
  options: {
    fullyTraverseArrays: false, // Default: false. By default, if an array starts with a primitive type, it will not be traversed. Set it to true if you want to capture scenarios in which lists can have intersped objects and primitives, e.g. [ 1, 2, "a", { important object } ]
    excludeProps: [ 'displayValue', 'displayMesh', '__closure' ] // Default: []. Any prop names that you pass in here will be ignored from object construction traversal. 
  }
} )

let obj = await loader.getAndConstructObject( ( e ) => console.log( 'Progress', e ) )

```

## Community

If in trouble, the Speckle Community hangs out on [the forum](https://speckle.community). Do join and introduce yourself! We're happy to help.

## License

Unless otherwise described, the code in this repository is licensed under the Apache-2.0 License. If you have any questions, don't hesitate to get in touch with us via [email](mailto:hello@speckle.systems).

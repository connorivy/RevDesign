function pluginMain() {
    var v = window.__viewer
    var maxLength = 0
    var maxLengthId = 0
    for (var index in v.sceneManager.sceneObjects.allSolidObjects.children) {
    // console.log(v.sceneManager.sceneObjects.allSolidObjects.children[index].userData.baseLine)
    var length = this.getLength(v.sceneManager.sceneObjects.allSolidObjects.children[index].userData)
    if (length > maxLength) {
        maxLength = length
        maxLengthId = v.sceneManager.sceneObjects.allSolidObjects.children[index].userData.id
    }
    }

    // // v.applyFilter({filterBy: {id : maxLengthId}, ghostOthers: true})
    this.$store.commit('isolateObjects', {
        filterKey: '__parents',
        filterValues: [maxLengthId]
    })
    console.log(maxLength, maxLengthId)
}
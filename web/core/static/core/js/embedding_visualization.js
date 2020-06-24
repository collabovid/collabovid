var colors = {
    "General": 0x424242,
    "Mechanism": 0x488f31,
    "Transmission": 0xbc5090,
    "Diagnosis": 0xc0af4a,
    "Treatment": 0xffa49c,
    "Prevention": 0x6d4c41,
    "Case Report": 0x009692,
    "Epidemic Forecasting": 0xde425b
}


function addPoints(points, object, atlas) {
    var geometry = new THREE.Geometry();
    for (var i = 0; i < points.length; i++) {
        var point = points[i];

        // Create x, y, z coords for this subimage
        var coords = {
            x: point.point[0],
            y: point.point[1],
            z: point.point[2] + 1
        };

        geometry.vertices.push(
            new THREE.Vector3(
                coords.x,
                coords.y,
                coords.z
            ),
            new THREE.Vector3(
                coords.x + object.width,
                coords.y,
                coords.z
            ),
            new THREE.Vector3(
                coords.x + object.width,
                coords.y + object.height,
                coords.z
            ),
            new THREE.Vector3(
                coords.x,
                coords.y + object.height,
                coords.z
            )
        );
        var maxScore = 0;
        var color = 0xffffff
        point.categories.forEach(function (item) {
            if (item.score > maxScore) {
                maxScore = item.score
                color = colors[item.name]
            }
        })

        var faces = [
            [0, 1, 2], [0, 2, 3],
        ];
        var nVertices = 4
        for (var j = 0; j < faces.length; j++) {
            var indices = faces[j];
            var face = new THREE.Face3(
                geometry.vertices.length - (nVertices - indices[0]),
                geometry.vertices.length - (nVertices - indices[1]),
                geometry.vertices.length - (nVertices - indices[2])
            );
            face.color = new THREE.Color(color);
            geometry.faces.push(face);
        }

        var idx = i % (atlas.rows * atlas.cols);
        var xOffset = (idx % atlas.rows) * (object.width / atlas.width);
        var yOffset = Math.floor(idx / atlas.cols) * (object.height / atlas.height);

        var xDistance = object.width / atlas.width
        var yDistance = object.height / atlas.height

        geometry.faceVertexUvs[0].push([
            new THREE.Vector2(xOffset, yOffset),
            new THREE.Vector2(xOffset + xDistance, yOffset),
            new THREE.Vector2(xOffset + xDistance, yOffset + yDistance)
        ]);

        geometry.faceVertexUvs[0].push([
            new THREE.Vector2(xOffset, yOffset),
            new THREE.Vector2(xOffset + xDistance, yOffset + yDistance),
            new THREE.Vector2(xOffset, yOffset + yDistance)
        ]);

    }
    return geometry;
}


var EmbeddingVisualization = function () {

    this.renderEmbeddings = function (canvas, onSelected, options) {
        var fieldOfView = 45;
        var scope = this;
        var aspectRatio = canvas.offsetWidth / canvas.offsetHeight;
        var nearPlane = 0.1;
        var farPlane = 1000;

        var camera = new THREE.PerspectiveCamera(
            fieldOfView, aspectRatio, nearPlane, farPlane
        );
        camera.position.z = 3.5;
        camera.position.x = 0;

        var renderer = new THREE.WebGLRenderer({canvas: canvas, alpha: true});
        renderer.setSize(canvas.offsetWidth, canvas.offsetHeight);

        var scene = new THREE.Scene();
        scene.background = null;

        var object = {width: 0.005, height: 0.005, depth: 0.005, color: 0x5475a1}
        var atlas = {cols: 10, rows: 10};
        atlas.width = object.width * atlas.cols
        atlas.height = object.height * atlas.rows

        var loader = new THREE.FileLoader();
        loader.load(options.fileUrl, function (data) {
            var paper = JSON.parse(data);
            scope.papers = paper;
            var geometry = addPoints(paper, object, atlas);

            var loader = new THREE.TextureLoader();
            var url = options.imageUrl;

            var material = new THREE.MeshBasicMaterial({
                map: loader.load(url),
                vertexColors: THREE.VertexColors
            });


            var mesh = new THREE.Mesh(geometry, material);
            mesh.position.set(-0.518, -0.547 / 2, -0.558)
            scene.add(mesh);


            var controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.zoomSpeed = 0.5
            controls.enableRotate = false
            controls.screenSpacePanning = true
            controls.mouseButtons = {
                LEFT: THREE.MOUSE.PAN,
                MIDDLE: THREE.MOUSE.DOLLY,
                RIGHT: THREE.MOUSE.DOLLY
            }
            controls.update()

            window.addEventListener('resize', function () {
                camera.aspect = canvas.offsetWidth / canvas.offsetHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(canvas.offsetWidth, canvas.offsetHeight);
                //controls.handleResize();
            });

            var light = new THREE.PointLight(0xffffff, 1, 10);
            light.position.set(1, 1, 10);
            scene.add(light)

            function animate() {
                requestAnimationFrame(animate);
                renderer.render(scene, camera);
                controls.update();
            }

            animate();

            var facesPerPoint = 2

            renderer.render(scene, camera);

            var raycaster = new THREE.Raycaster();
            var mouse = new THREE.Vector2();

            scope.selectedFaces = [];

            function onMouseMove(event) {
                var rect = canvas.getBoundingClientRect(),
                    x = event.clientX - rect.left,
                    y = event.clientY - rect.top;
                // convert x,y to clip space; coords from top left, clockwise:
                // (-1,1), (1,1), (-1,-1), (1, -1)
                var mouse = new THREE.Vector3();
                mouse.x = ((x / canvas.clientWidth) * 2) - 1;
                mouse.y = (-(y / canvas.clientHeight) * 2) + 1;
                raycaster.setFromCamera(mouse, camera);
                var intersects = raycaster.intersectObjects(scene.children);
                if (intersects.length > 0) {
                    scope.selectedFaces.forEach(function (face) {
                        face.color = new THREE.Color(0xffffff);
                    })
                    scope.selectedFaces = [];

                    var faceIndex = intersects[0].faceIndex;
                    var pointIndex = Math.floor(faceIndex / facesPerPoint);
                    var faceStartIndex = pointIndex * facesPerPoint
                    geometry.faces[faceIndex].color = new THREE.Color(0xDF1544);

                    for (var idx = faceStartIndex; idx < faceStartIndex + facesPerPoint; idx++) {
                        geometry.faces[idx].color = new THREE.Color(0xDF1544);
                        scope.selectedFaces.push(geometry.faces[idx])
                    }
                    onSelected(paper[pointIndex])

                    geometry.colorsNeedUpdate = true
                    geometry.elementsNeedUpdate = true
                    renderer.render(scene, camera);
                }
            }

            window.addEventListener('mousedown', onMouseMove, false);
            scope.geometry = geometry;
            scope.renderer = renderer;
            scope.scene = scene;
            scope.camera = camera;
        })
    }

    this.computeNeighbors = function (paper, n) {
        var min_distances = new Array(n).fill(null);
        var min_indices = new Array(n).fill(null)
        for (var i = 0; i < this.papers.length; i++) {
            if (paper === this.papers[i]) {
                continue;
            }
            var other = this.papers[i];
            var distance = math.distance(paper.point, other.point);
            var added = false;
            for (var j = 0; j < min_indices.length; j++) {
                if (min_distances[j] == null) {
                    min_distances[j] = distance
                    min_indices[j] = i
                    added = true
                    break
                }
            }
            if (!added) {
                for (var j = 0; j < min_indices.length; j++) {
                    if (min_distances[j] > distance) {
                        min_distances[j] = distance
                        min_indices[j] = i
                        break
                    }
                }
            }
        }
        return min_indices
    }

    this.markWithColor = function (paperIndices) {
        for (var i = 0; i < paperIndices.length; i++) {
            var faceStartIndex = paperIndices[i] * 2
            for (var idx = faceStartIndex; idx < faceStartIndex + 2; idx++) {
                this.geometry.faces[idx].color = new THREE.Color(0x9da832);
                this.selectedFaces.push(this.geometry.faces[idx])
            }
        }
        this.geometry.colorsNeedUpdate = true
        this.geometry.elementsNeedUpdate = true
        this.renderer.render(this.scene, this.camera);
    }
}
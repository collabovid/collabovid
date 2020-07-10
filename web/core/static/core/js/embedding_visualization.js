const EmbeddingVisualization = function () {

        const paperProperties = {width: 0.005, height: 0.005, depth: 0.005, color: 0x5475a1};
        const atlasImage = {cols: 10, rows: 10};
        atlasImage.width = paperProperties.width * atlasImage.cols;
        atlasImage.height = paperProperties.height * atlasImage.rows;


        this.buildGeometry = function (papers) {
            const geometry = new THREE.Geometry();
            for (let i = 0; i < papers.length; i++) {
                let paper = papers[i];

                let coords = {
                    x: paper.point[0],
                    y: paper.point[1],
                    z: paper.point[2] + 1
                };

                geometry.vertices.push(
                    new THREE.Vector3(
                        coords.x,
                        coords.y,
                        coords.z
                    ),
                    new THREE.Vector3(
                        coords.x + paperProperties.width,
                        coords.y,
                        coords.z
                    ),
                    new THREE.Vector3(
                        coords.x + paperProperties.width,
                        coords.y + paperProperties.height,
                        coords.z
                    ),
                    new THREE.Vector3(
                        coords.x,
                        coords.y + paperProperties.height,
                        coords.z
                    )
                );
                let color = this.getColorForPaper(paper);
                let faces = [
                    [0, 1, 2], [0, 2, 3],
                ];
                let nVertices = 4;
                for (let j = 0; j < faces.length; j++) {
                    let indices = faces[j];
                    let face = new THREE.Face3(
                        geometry.vertices.length - (nVertices - indices[0]),
                        geometry.vertices.length - (nVertices - indices[1]),
                        geometry.vertices.length - (nVertices - indices[2])
                    );
                    face.color = new THREE.Color(color);
                    face.materialIndex = 0;
                    geometry.faces.push(face);
                }

                // find image coordinates in atlas image
                let idx = i % (atlasImage.rows * atlasImage.cols);
                let xOffset = (idx % atlasImage.rows) * (paperProperties.width / atlasImage.width);
                let yOffset = Math.floor(idx / atlasImage.cols) * (paperProperties.height / atlasImage.height);
                let xDistance = paperProperties.width / atlasImage.width;
                let yDistance = paperProperties.height / atlasImage.height;
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
        };

        this.renderEmbeddings = function (canvas, onSelected, options) {
            let fieldOfView = 75;
            let scope = this;
            let aspectRatio = canvas.offsetWidth / canvas.offsetHeight;
            let nearPlane = 0.001;
            let farPlane = 1000;

            let camera = new THREE.PerspectiveCamera(
                fieldOfView, aspectRatio, nearPlane, farPlane
            );
            camera.position.z = 2.5;
            camera.position.x = 0;

            let renderer = new THREE.WebGLRenderer({canvas: canvas, alpha: true});
            const container = document.getElementById('canvas-container');
            renderer.setSize(container.offsetWidth, container.offsetHeight);

            let scene = new THREE.Scene();
            scene.background = null;

            let loader = new THREE.FileLoader();
            loader.load(options.fileUrl, function (data) {
                let paperData = JSON.parse(data);
                let papers = paperData.papers;
                let geometry = scope.buildGeometry(papers);
                let loader = new THREE.TextureLoader();
                let url = options.imageUrl;

                // materials with different level of opacity to change opacity for individual faces
                let opacMaterial = new THREE.MeshBasicMaterial({
                    transparent: true,
                    opacity: 0.1,
                    map: loader.load(url),
                    vertexColors: THREE.VertexColors
                });
                let halfOpacMaterial = new THREE.MeshBasicMaterial({
                    transparent: true,
                    opacity: 0.5,
                    map: loader.load(url),
                    vertexColors: THREE.VertexColors
                });
                let solidMaterial = new THREE.MeshBasicMaterial({
                    transparent: false,
                    map: loader.load(url),
                    vertexColors: THREE.VertexColors
                });
                let material = new THREE.MultiMaterial([solidMaterial, halfOpacMaterial, opacMaterial]);
                let mesh = new THREE.Mesh(geometry, material);
                //mesh.position.set(-paperData.means[0], -paperData.means[1] / 4, -paperData.means[2])
                scene.add(mesh);

                let controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.zoomSpeed = options.zoomSpeed;
                controls.panSpeed = options.panSpeed;

                controls.enableRotate = false;
                controls.screenSpacePanning = true;
                controls.mouseButtons = {
                    LEFT: THREE.MOUSE.PAN,
                    MIDDLE: THREE.MOUSE.DOLLY,
                    RIGHT: THREE.MOUSE.DOLLY
                };
                controls.touches = {
                    ONE: THREE.TOUCH.PAN,
                    TWO: THREE.TOUCH.DOLLY_PAN
                };
                controls.update();

                // handle resize of window
                window.addEventListener('resize', function () {
                    camera.aspect = window.innerWidth / canvas.offsetHeight;
                    camera.updateProjectionMatrix();
                    controls.update();
                    const container = document.getElementById('canvas-container');

                    renderer.setSize(container.offsetWidth, container.offsetHeight);
                });

                // setup the light
                let light = new THREE.PointLight(0xffffff, 1, 10);
                light.position.set(1, 1, 10);
                scene.add(light);

                // animation loop
                function animate(time) {
                    requestAnimationFrame(animate);
                    TWEEN.update(time);
                    renderer.render(scene, camera);
                    if (!scope.animating) {
                        controls.update();
                    }
                }

                requestAnimationFrame(animate);


                let raycaster = new THREE.Raycaster();
                const facesPerPoint = 2;

                // gets called when there is a click event
                function onClick(x, y) {
                    let rect = canvas.getBoundingClientRect();
                    x = x - rect.left;
                    y = y - rect.top;
                    let mouse = new THREE.Vector3();
                    mouse.x = ((x / canvas.clientWidth) * 2) - 1;
                    mouse.y = (-(y / canvas.clientHeight) * 2) + 1;
                    raycaster.setFromCamera(mouse, camera);
                    let intersects = raycaster.intersectObjects(scene.children);
                    if (intersects.length > 0) {
                        let faceIndex = intersects[0].faceIndex;
                        let pointIndex = Math.floor(faceIndex / facesPerPoint);
                        let faceStartIndex = pointIndex * facesPerPoint;
                        geometry.faces[faceIndex].color = new THREE.Color(0xDF1544);

                        for (let idx = faceStartIndex; idx < faceStartIndex + facesPerPoint; idx++) {
                            geometry.faces[idx].color = new THREE.Color(0xDF1544);
                        }
                        onSelected(pointIndex, papers[pointIndex]);

                        geometry.colorsNeedUpdate = true;
                        geometry.elementsNeedUpdate = true;
                        renderer.render(scene, camera);
                    } else {
                        scope.deselectAll();
                    }
                }

                // setup listener that only fires on a single click event (no dragging etc.)
                const delta = 6;
                let startX;
                let startY;
                renderer.domElement.addEventListener('mousedown', function (event) {
                    startX = event.pageX;
                    startY = event.pageY;
                });
                renderer.domElement.addEventListener('mouseup', function (event) {
                    const diffX = Math.abs(event.pageX - startX);
                    const diffY = Math.abs(event.pageY - startY);

                    if (diffX < delta && diffY < delta) {
                        onClick(event.clientX, event.clientY);
                    }
                });

                renderer.domElement.addEventListener('touchstart', function (event) {
                    startX = event.changedTouches[0].pageX;
                    startY = event.changedTouches[0].pageY;
                });


                renderer.domElement.addEventListener('touchend', function (event) {
                    const diffX = Math.abs(event.changedTouches[0].pageX - startX);
                    const diffY = Math.abs(event.changedTouches[0].pageY - startY);

                    if (diffX < delta && diffY < delta) {
                        onClick(event.changedTouches[0].clientX, event.changedTouches[0].clientY);
                    }
                });


                scope.geometry = geometry;
                scope.renderer = renderer;
                scope.scene = scene;
                scope.papers = papers;
                scope.controls = controls;
                scope.material = material;
                scope.camera = camera;
                scope.paperData = paperData;

                scope.viewArea(paperData.means[0], paperData.means[1], paperData.means[2] + 2.5)
            })
        }
        ;

        this.repaintElements = function () {
            this.geometry.faces[0].color = new THREE.Color(0xcc7a00);
            this.geometry.colorsNeedUpdate = true;
            this.geometry.elementsNeedUpdate = true;
            this.renderer.render(this.scene, this.camera);
            console.log("CHANGED");
        };

        this.onDeselect = function (callback) {
            this.onDeselectCallback = callback;
        };

        this.computeNeighbors = function (paper, n) {
            let min_distances = new Array(n).fill(null);
            let min_indices = new Array(n).fill(null);
            for (let i = 0; i < this.papers.length; i++) {
                if (paper === this.papers[i]) {
                    continue;
                }
                let other = this.papers[i];
                let distance = math.distance(paper.point, other.point);
                let added = false;
                for (let j = 0; j < min_indices.length; j++) {
                    if (min_distances[j] == null) {
                        min_distances[j] = distance;
                        min_indices[j] = i;
                        added = true;
                        break
                    }
                }
                if (!added) {
                    for (let j = 0; j < min_indices.length; j++) {
                        if (min_distances[j] > distance) {
                            min_distances[j] = distance;
                            min_indices[j] = i;
                            break
                        }
                    }
                }
            }
            return min_indices
        };

        this.getColorForPaper = function (paper) {
            let color = 0xffffff;
            const category = this.getHighestCategoryForPaper(paper);
            if (category) {
                color = colors[category]
            }
            return color;
        };

        this.getHighestCategoryForPaper = function (paper) {
            return paper.categories[paper.top_category_index].name
        };

        this.deselectAll = function () {
            for (let i = 0; i < this.papers.length; i++) {
                let color = this.getColorForPaper(this.papers[i]);
                let materialIndex = 0;
                let faceStartIndex = i * 2;
                for (let idx = faceStartIndex; idx < faceStartIndex + 2; idx++) {
                    this.geometry.faces[idx].color = new THREE.Color(color);
                    this.geometry.faces[idx].materialIndex = materialIndex
                }
            }
            this.geometry.colorsNeedUpdate = true;
            this.geometry.elementsNeedUpdate = true;
            this.renderer.render(this.scene, this.camera);
            if (this.onDeselectCallback) {
                this.onDeselectCallback();
            }
        };

        this.selectPaper = function (paperIndex, neighborIndices) {
            for (let i = 0; i < this.papers.length; i++) {
                let color = 0xffffff;
                let materialIndex = 2;
                if (neighborIndices.includes(i)) {
                    color = 0xcc7a00;
                    materialIndex = 1;
                }
                if (paperIndex === i) {
                    color = 0xffc266;
                    materialIndex = 0
                }
                let faceStartIndex = i * 2;
                for (let idx = faceStartIndex; idx < faceStartIndex + 2; idx++) {
                    this.geometry.faces[idx].color = new THREE.Color(color);
                    this.geometry.faces[idx].materialIndex = materialIndex
                }
            }
            this.geometry.colorsNeedUpdate = true;
            this.geometry.elementsNeedUpdate = true;
            this.renderer.render(this.scene, this.camera);
        };

        this.viewArea = function (x, y, z) {
            this.camera.position.x = x;
            this.camera.position.y = y;
            this.camera.position.z = z;
            this.controls.target.set(x, y, z - 5);
            this.camera.lookAt(x, y, z - 5);
            this.camera.rotation.z = 0;
            this.camera.rotation.x = 0;
            this.camera.rotation.y = 0;
            this.camera.updateProjectionMatrix();
        };

        this.selectPapers = function (dois, selectionColor) {
            let minCoordinates = new Array(3).fill(100000);
            let maxCoordinates = new Array(3).fill(-10000);
            for (let i = 0; i < this.papers.length; i++) {
                let color = 0xffffff;
                let materialIndex = 2;
                if (dois.includes(this.papers[i].doi)) {
                    color = selectionColor;
                    materialIndex = 0;
                    for (let j = 0; j < 3; j++) {
                        minCoordinates[j] = Math.min(this.papers[i].point[j], minCoordinates[j]);
                        maxCoordinates[j] = Math.max(this.papers[i].point[j], maxCoordinates[j])
                    }
                }
                let faceStartIndex = i * 2;
                for (let idx = faceStartIndex; idx < faceStartIndex + 2; idx++) {
                    this.geometry.faces[idx].color = new THREE.Color(color);
                    this.geometry.faces[idx].materialIndex = materialIndex
                }
            }
            this.geometry.colorsNeedUpdate = true;
            this.geometry.elementsNeedUpdate = true;

            let newX = minCoordinates[0] + (maxCoordinates[0] - minCoordinates[0]) / 2.0;
            let newY = minCoordinates[1] + (maxCoordinates[1] - minCoordinates[1]) / 2.0;
            let newZ = maxCoordinates[2] + 2;

            const coords = {x: this.camera.position.x, y: this.camera.position.y, z: this.camera.position.z};
            this.animating = true;
            const tween = new TWEEN.Tween(coords)
                .to({
                    x: newX,
                    y: newY,
                    z: newZ
                }, 1200)
                .easing(TWEEN.Easing.Quadratic.Out)
                .onUpdate(() => {
                    this.viewArea(coords.x, coords.y, coords.z)
                }).onComplete(() => {
                    this.animating = false;
                }).start()
        }
    }
;
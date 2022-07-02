from browser import alert, window, ajax
from javascript import JSON


class MapRenderer:
    def __init__(self, center, zoom, get_location_url, camera_view_url):
        self.center = center
        self.zoom = zoom
        # get data
        self.leaflet = window.L
        self.shapes = {}

        self.markers = None
        self.user_coord = None
        self.user_mark = []
        self.get_location_url = get_location_url
        self.camera_view_url = camera_view_url

        self.openstreet = self.leaflet.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                "maxZoom": 19,
                "attribution": """&copy;
                <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors""",
            },
        )
        self.positron = self.leaflet.tileLayer(
            "https://{s}.basemaps.cartocdn.com/rastertiles/light_all/{z}/{x}/{y}.png",
            {
                "attribution": """&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors,
                                &copy; <a href="http://cartodb.com/attributions">CartoDB</a>""",
                "subdomains": "abcd",
                "maxZoom": 19,
            },
        )
        self.world_imagery = self.leaflet.tileLayer(
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            {
                "maxZoom": 17,
                "attribution": """Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye,
                 Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community""",
            },
        )
        self.world_topo = self.leaflet.tileLayer(
            """https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}""",
            {
                "attribution": """Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap,
                 iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, Ordnance Survey, Esri Japan, METI,
                 Esri China (Hong Kong), and the GIS User Community"""
            },
        )
        self.base_maps = {
            "<b><span style='color: grey'>Positron</span></b>": self.positron,
            "<b><span style='color: blue'>OpenStreet Map</span></b>": self.openstreet,
            "<b><span style='color: green'>World Map</span></b>": self.world_imagery,
            "<b><span style='color: teal'>World Topo Map</span></b>": self.world_topo,
        }
        self.map = self.leaflet.map(
            "mapbrython",
            {
                "center": self.center,
                "zoom": self.zoom,
                "layers": self.positron,
                "renderer": self.leaflet.canvas({"padding": 0.5}),
                "smoothWheelZoom": True,  # enable smooth zoom
                "smoothSensitivity": 1,  # zoom speed. default is 1
            },
        )

        def navi(pos):
            self.user_coord = (pos.coords.latitude, pos.coords.longitude)
            self.user_mark = (
                self.leaflet.marker(
                    self.user_coord,
                    {"icon": self.get_icon("my_location"), "zIndexOffset": 1000},
                )
                .addTo(self.map)
                .bindPopup("ตำแหน่งของคุณ")
            )

        def nonavi(error):
            alert("Your browser doesn't support geolocation")

        window.navigator.geolocation.getCurrentPosition(
            navi, nonavi
        )  # set user's current location on map(success, error)

        self.leaflet.control.layers(self.base_maps).addTo(self.map)

    def fly_to_user(self):
        self.map.flyTo(self.user_coord, 16)
        self.user_mark.openPopup()

    def zoom_out(self):
        self.map.zoomOut(1)

    def zoom_in(self):
        self.map.zoomIn(1)

    def on_each_feature(self, feature, layer):  # feature = layer.feature
        def zoom_to_feature(e):
            if self.map.getZoom() < 11:
                self.map.fitBounds(e.target.getBounds())

        def reset_highlight(e):
            for key in self.shapes:
                if self.shapes[key].hasLayer(layer):
                    self.shapes[key].resetStyle(e.target)

        def highlight_feature(e):
            layer = e.target

            layer.setStyle(
                {"weight": 2, "color": "black", "dashArray": "", "fillOpacity": 0.8}
            )

        layer.on(
            {
                "mouseover": highlight_feature,
                "mouseout": reset_highlight,
                "click": zoom_to_feature,
            }
        )

    def get_icon(self, type="mark_white", size=[35, 35]):
        return self.leaflet.icon(
            dict(
                iconUrl=f"/static/brython/maps/resources/marks/{type}.svg",
                iconSize=size,
                iconAnchor=[22, 40],
                popupAnchor=[0, -30],
            )
        )

    def set_camera_marker(self, data):
        layers = []

        def on_click_device(camera_id):
            window.location.href = f"{self.camera_view_url}&camera_id={camera_id}"

        camera_icon = self.get_icon(type="camera_marker", size=[80, 80])
        for camera_data in data:
            tooltip_detail = f"""<div align="left" style="font-size: 15px;"> <b>{camera_data["name"]}</b>"""
            print(camera_data["location"][1])

            marker = (
                self.leaflet.marker(
                    [camera_data["location"][1], camera_data["location"][0]],
                    {
                        "customId": camera_data["camera_id"],
                        "icon": camera_icon,
                    },
                )
                .bindTooltip(
                    tooltip_detail,
                    {"offset": (0, 30), "className": "tooltip-marker"},
                )
                .addTo(self.map)
                .on("click", lambda e: on_click_device(e.sourceTarget.options.customId))
            )
            layers.append(marker)

        self.leaflet.layerGroup(layers).addTo(self.map)

    def on_get_data_complete(self, res):
        data = JSON.parse(res.text)
        self.set_camera_marker(data)
        # print(data)

    def start(self):
        ajax.get(self.get_location_url, oncomplete=self.on_get_data_complete)
        # print(self.get_location_url)

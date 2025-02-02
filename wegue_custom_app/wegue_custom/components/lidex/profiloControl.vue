<template>

  <div id="profili_panel">
    <div ref="element" class="options">
    </div>
    <div ref="title" class="profili_title">
      {{ theme }}
    </div>
  </div>

</template>

<script>
import { Mapable } from '../../../src/mixins/Mapable';
import { WguEventBus } from '@/WguEventBus';
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import Style from 'ol/style/Style';
import Stroke from 'ol/style/Stroke';
import Circle from 'ol/style/Circle';
import Fill from 'ol/style/Fill';
import Hover from 'ol-ext/interaction/Hover';
import Point from 'ol/geom/Point';
import Feature from 'ol/Feature';
import Profile from 'ol-ext/control/Profile';

export default {
  name: 'wgu-profilo-control',
  inheritAttrs: false,
  components: {
  },
  mixins: [Mapable],
  props: {
    theme: { type: String, required: true },
    selectable: { type: Boolean, required: false, default: false },
    zoomable: { type: Boolean, required: false, default: false }
  },
  data () {
    return {
      moduleName: 'wgu-profilo-control',
      hover: undefined,
      feature: undefined,
      pt: undefined,
      profileCtrl: undefined,
      profileElement: undefined,
      profileOverlay: undefined
    }
  },

  created () {
    console.log('CREATED', this.theme)
    const eventId = 'wgu-profile-feature-' + this.theme
    WguEventBus.$on(eventId, this.applyProfileFeature)
    WguEventBus.$on('wgu-profile-cursor', this.applyCursor)
  },

  unmounted () {
    console.log('UNMOUNTED')
  },

  activated () {
    console.log('ACTIVATED')
  },

  deactivated () {
    console.log('DEACTIVATED')
  },

  beforeDestroy () {
    console.log('DESTROYED', this.theme)
    this.applyProfileFeature(undefined)
    this.map.removeLayer(this.profileOverlay);
    this.map.removeInteraction(this.hover);
    this.map.removeControl(this.profileCtrl);
  },

  mounted () {
    const me = this
    console.log('mounted', this.theme, this)

    this.profileOverlay = new VectorLayer({
      source: new VectorSource(
        { projection: 'EPSG:32632' }
      ),
      title: 'profilo',
      visible: true,
      style: new Style({
        stroke: new Stroke({
          color: '#0044FF',
          width: 3
        }),
        fill: new Fill({
          color: 'rgba(255, 255, 255, 0.2)'
        }),
        image: new Circle({
          radius: 4,
          fill: new Fill({
            color: '#0044FF'
          })
        })
      })
    });

    this.map.addLayer(this.profileOverlay);

    this.profileCtrl = new Profile({
      target: me.$refs.element,
      selectable: this.selectable,
      zoomable: this.zoomable,
      style: new Style({
        fill: new Fill({ color: '#ccc' })
      }),
      title: 'DSM',
      height: 150,
      width: 600
    });

    this.map.addControl(this.profileCtrl);

    function drawPoint (e) {
      if (!me.pt) return;
      if (e.type === 'over') {
        // Show point at coord
        me.pt.setGeometry(new Point([e.coord[0], e.coord[1]]));
        me.pt.setStyle(null);
      } else {
        // hide point
        me.pt.setStyle([]);
      }
    };

    this.profileCtrl.on(['over', 'out'], function (e) {
      if (e.type === 'over') WguEventBus.$emit('wgu-profile-cursor', e.coord)
      if (e.coord) {
        const tc = new Point(e.coord)
        tc.transform('EPSG:7792', 'EPSG:7792')
        drawPoint({ type: 'over', coord: tc.getCoordinates() });
      }
      me.profileCtrl.showAt(e.distance)
    });

    this.hover = new Hover({
      cursor: 'pointer',
      hitTolerance: 10,
      layers: [me.profileOverlay]
    });

    this.map.addInteraction(this.hover);

    this.hover.on('hover', function (e) {
      // Point on the line
      if (!me.feature) return
      const c = me.feature.getGeometry().getClosestPoint(e.coordinate)
      drawPoint({ type: 'over', coord: c });
      // Show profil
      const tc = new Point(c)
      tc.transform('EPSG:7792', 'EPSG:7792')
      WguEventBus.$emit('wgu-profile-cursor', tc.getCoordinates())
    });

    this.hover.on('leave', function (e) {
      me.profileCtrl.popup();
      me.profileCtrl.showAt();
      drawPoint({});
    });
  },

  methods: {
    /**
       * (Un-)Register map interactions when the visibility of the module changes.
       *
       * @param  {boolean} visible New visibility state
       */
    show (visible) {

    },
    applyCursor (coords) {
      console.log(coords)
      if (coords) {
        const p = this.profileCtrl.showAt(coords);
        this.profileCtrl.popup(p[2] + ' m');
      }
    },

    detach () {
    },

    /**
       * Applies the changed measure value to this.measureType.
       * Called as callback of MeasureTypeChooser
       *
       * @param  {String} newMeasureType New measure type
       * @param  {String} oldMeasureType Old measure type
       */
    applyProfileFeature (feature) {
      console.log('incoming feature', this.theme, feature)
      this.feature = feature

      if (feature) {
        console.log(feature.getGeometry().getCoordinates())
        this.active = true
        this.profileOverlay.getSource().clear()
        this.profileOverlay.getSource().addFeature(feature)
        this.profileCtrl.setGeometry(feature, {
          graduation: 50,
          zmin: 0
        });
        this.pt = new Feature(new Point([0, 0]));
        this.pt.setStyle([]);
        this.profileOverlay.getSource().addFeature(this.pt);
        const geomgbo = feature.getGeometry();
        geomgbo.transform('EPSG:7792', 'EPSG:7792');
        // const grow = buffer(geomgbo.getExtent(), 100)
        // this.map.getView().fit(geomgbo.getExtent());
        // console.log(geomgbo.getExtent())
      } else {
        this.profileOverlay.getSource().clear()
      }
    },
    /**
       * This function is executed, after the map is bound (see mixins/Mapable)
       */
    onMapBound () {
      console.log('MAPBOUND')
    },
    /**
       * This function is executed, after the map is bound (see mixins/Mapable)
       */
    onMapUnbound () {
      console.log('MAPUNBOUND')
    }
  }
}
</script>
<style scoped>

.profili_title {
  bottom: 5px;
  left: 5px;
  font-size: 18px;
  font-weight: bold;
  position: relative;
}

#profili_panel {
  width: 100%;
  min-height: 200px;
  font-size: 10px !important;
  background-color: beige;
  margin-top: 10px;
}

</style>
<style>
.ol-profile {
  position:relative;
  -webkit-user-select:none;
  -moz-user-select:none;
  -ms-user-select:none;
  user-select:none
}
.ol-control.ol-profile {
  position:absolute;
  top:.5em;
  right:3em;
  text-align:right;
  overflow:hidden
}
.ol-profile .ol-zoom-out {
  position:absolute;
  top:10px;
  right:10px;
  width:1em;
  height:1em;
  padding:0;
  border:1px solid #000;
  border-radius:2px;
  cursor:pointer
}
.ol-profile .ol-zoom-out:before {
  content:'';
  height:2px;
  width:60%;
  background:currentColor;
  position:absolute;
  left:50%;
  top:50%;
  -webkit-transform:translate(-50%,-50%);
  transform:translate(-50%,-50%)
}
.ol-profile .ol-inner {
  position:relative;
  padding:.5em;
  font-size:.8em
}
.ol-control.ol-profile .ol-inner {
  display:block;
  background-color:rgba(255,255,255,.7);
  margin:2.3em 2px 2px
}
.ol-control.ol-profile.ol-collapsed .ol-inner {
  display:none
}
.ol-profile canvas {
  display:block
}
.ol-profile button {
  display:block;
  position:absolute;
  right:0;
  overflow:hidden
}
.ol-profile button i {
  position:absolute;
  left:50%;
  top:50%;
  -webkit-transform:translate(-50%,-50%);
  transform:translate(-50%,-50%);
  width:1em;
  height:1em;
  overflow:hidden
}
.ol-profile button i:after,
.ol-profile button i:before {
  content:"";
  position:absolute;
  display:block;
  background-color:currentColor;
  width:1em;
  height:.9em;
  -webkit-transform:scaleX(.8) translate(-.25em,.5em) rotate(45deg);
  transform:scaleX(.8) translate(-.25em,.5em) rotate(45deg)
}
.ol-profile button i:after {
  -webkit-transform:scaleX(.8) translate(.35em,.7em) rotate(45deg);
  transform:scaleX(.8) translate(.35em,.7em) rotate(45deg)
}
.ol-profile.ol-collapsed button {
  position:static
}
.ol-profile .ol-profilebar,
.ol-profile .ol-profilecursor {
  position:absolute;
  pointer-events:none;
  width:1px;
  display:none
}
.ol-profile .ol-profilecursor {
  width:0;
  height:0
}
.ol-profile .ol-profilecursor:before {
  content:"";
  pointer-events:none;
  display:block;
  margin:-2px;
  width:5px;
  height:5px
}
.ol-profile .ol-profilebar,
.ol-profile .ol-profilecursor:before {
  background:red
}
.ol-profile table {
  text-align:center;
  width:100%
}
.ol-profile table span {
  display:block
}
.ol-profilepopup {
  background-color:rgba(255,255,255,.5);
  margin:.5em;
  padding:0 .5em;
  font-size: 18px;
  position:absolute;
  top:-1em;
  white-space:nowrap
}
.ol-profilepopup.ol-left {
  right:0
}
.ol-profile table td {
  padding:0 2px
}
.ol-profile table .track-info {
  display:table-row
}
.ol-profile .over table .track-info,
.ol-profile table .point-info {
  display:none
}
.ol-profile .over table .point-info {
  display:table-row
}
.ol-control.ol-routing.ol-collapsed .content,
.ol-progress-bar>.ol-waiting,
.ol-routing .ol-search ul .copy,
.ol-routing .ol-search.ol-collapsed ul {
  display:none
}
.ol-profile p {
  text-align:center;
  margin:0
}
</style>

<!-- The template contains the HTML of our module  -->
<template>
  <!--  eslint-disable  -->
  <!--
  Our module builds upon the 'wgu-module-card'
  it handles the integration into Wegue
  like adding a button in the toolbar
  -->
  <wgu-module-card
    v-bind="$attrs"
    moduleName="wgu-profili"
    class="wgu-profili"
    :icon="icon"
    v-on:visibility-change="show"
    ref="card"
  >
    <v-card-title primary-title class="wgu-profili-win-title">
      {{ $t("wgu-profili.selectionTitle") }}
    </v-card-title>
    <!--
    Here goes the actual content of the module
    We use a the component 'v-card-text' from the Vuetify library
    -->
    <v-card-text  height="500">
      <!--
      Note the double curly brackets.
      They contain variables that dynamically change.
      The way how they change is done in the <script> part
      -->
      <div style="padding-top: 15px;"></div>
      <wgu-profilo-control
        theme="DTM"
        selectable
        zoomable
        v-show="profileOk"
      ></wgu-profilo-control>
      <wgu-profilo-control
        theme="DSM"
        selectable
        zoomable
        v-show="profileOk"
      ></wgu-profilo-control>
      <div style="padding-top: 15px;"></div>
      <v-btn large block value="dl" v-if="profileOk" v-on:click="download" rounded color="primary">
        <span >
            {{ $t("wgu-profili.download") }}
          </span>
      </v-btn>
    </v-card-text>
  </wgu-module-card>
</template>
<script>
// the module card is a the template for a typical Wegue module
import ModuleCard from '../../../src/components/modulecore/ModuleCard';
// we import a so called "mixin" that helps us to interact with the map
import { Mapable } from '../../../src/mixins/Mapable';
// an OpenLayer helper function to transform coordinate reference systems
import profiloControl from './profiloControl';
import Draw from 'ol/interaction/Draw';
import { WguEventBus } from '@/WguEventBus';
import axios from 'axios';
import Style from 'ol/style/Style';
import Stroke from 'ol/style/Stroke';
import WKT from 'ol/format/WKT';

export default {
  name: 'wgu-profili-win',
  // make sure to register the 'Mapable' mixin
  mixins: [Mapable],
  inheritAttrs: false,
  components: {
    'wgu-module-card': ModuleCard,
    'wgu-profilo-control': profiloControl
  },
  props: {
  },
  // here we define variables that are used in the HTML above
  data () {
    return {
      icon: '',
      profileOk: false
    };
  },

  watch: {
    // listen to changed measurement type and forward to parent component
    selectTypeData (newVal, oldVal) {
      console.log('selectTypeData')
      console.log('changed', newVal)
      this.$emit('wgu-selecttype-change', newVal, oldVal);
      if (this.olMapCtrl) this.olMapCtrl.addInteraction(newVal, this.onEndSelect);
    }
  },

  methods: {
    /**
     * This function is called once the map is bound to the application
     */
    onMapBound () {
    },
    /**
       * This function is executed, after the map is bound (see mixins/Mapable)
       */
    onMapUnbound () {
    },

    show (visible) {
      console.log('SHOW', this.map.getView().getZoom())
      this.profileOk = false
      const me = this

      if (visible) {
        WguEventBus.$emit('wgu-start-menu-one-window', this.$refs.card.moduleName + '-win');
        this.drawLine = new Draw({
          // source: selectionOverlay,
          type: 'LineString',
          maxPoints: 2,
          style: function styleFunction (feature) {
            return new Style({
              stroke: new Stroke({
                color: 'blue',
                width: 5
              })
            })
          }
        })

        this.drawLine.on('drawstart', function () {
          WguEventBus.$emit('wgu-profile-feature-DTM', undefined)
          WguEventBus.$emit('wgu-profile-feature-DSM', undefined)
        })

        this.drawLine.on('drawend', function (event) {
          const profileLine = event.feature.getGeometry()
          profileLine.transform(process.env.VUE_APP_INTERFACE_SRS, process.env.VUE_APP_COVERAGE_SRS)
          const coords = profileLine.getCoordinates()
          console.log(coords)
          console.log('drawend', coords)
          const url = process.env.VUE_APP_LIDEX + '/profilo/dtm/'
          axios.post(url, { line: coords })
            .then(response => {
              console.log(response)
              me.response = response.data
              const converter = new WKT({ dataProjection: process.env.VUE_APP_COVERAGE_SRS, featureProjection: process.env.VUE_APP_INTERFACE_SRS })
              const dtmfeat = converter.readFeature(response.data.output.dtm.wkt)
              const dsmfeat = converter.readFeature(response.data.output.dsm.wkt)
              me.profileOk = true

              WguEventBus.$emit('wgu-profile-feature-DTM', dtmfeat)
              WguEventBus.$emit('wgu-profile-feature-DSM', dsmfeat)
            }).catch(console.error)
        })

        this.map.addInteraction(this.drawLine);
      } else {
        this.map.removeInteraction(this.drawLine);
      }
    },

    download () {
      window.open(this.response.dxf, '_blank');
    }

  }
};
</script>
<!-- Here we do the styling of our module -->
<style scoped>
/* our module has the class '.sample-module' and we reference it here */
.wgu-profili.wgu-floating {
  min-width: 600px;
}

.v-btn-toggle {
  flex-direction: column;
  min-width: 100%;
}
.v-btn {
  width: 100%;
}
span {
  padding-left: 10px;
  padding-right: 10px;
}
</style>

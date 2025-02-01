<!-- The template contains the HTML of our module  -->
<template>
  <!--
  Our module builds upon the 'wgu-module-card'
  it handles the integration into Wegue
  like adding a button in the toolbar
  -->
  <wgu-module-card
    v-bind="$attrs"
    moduleName="wgu-getPointCloud"
    class="wgu-getPointCloud"
    :icon="icon"
    v-on:visibility-change="show"
    ref="card"
  >
    <v-card-title primary-title class="wgu-getPointCloud-win-title">
      {{ $t("wgu-getPointCloud.selectionTitle") }}
    </v-card-title>

    <v-progress-circular
          :width="3"
          indeterminate
          v-if="loading"
        ></v-progress-circular>
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
      <v-btn-toggle color="secondary" v-model="selectTypeData" mandatory>
        <v-btn value="box">
          <v-icon>
            mdi-vector-square
          </v-icon>
          <span v-if="!iconsOnly">
            {{ $t("wgu-getPointCloud.selectBox") }}
          </span>
        </v-btn>
        <v-btn value="poly">
          <v-icon>
            mdi-vector-polygon
          </v-icon>
          <span v-if="!iconsOnly">
            {{ $t("wgu-getPointCloud.selectPoly") }}
          </span>
        </v-btn>
      </v-btn-toggle>
      <div style="padding-top: 15px;"></div>
      <v-btn large block value="dl" v-if="response" v-on:click="download" rounded color="primary">
        <span >
            {{ $t("wgu-getPointCloud.download") }}
          </span>
      </v-btn>
      <div style="padding-top: 5px;"></div>
      <v-btn large block value="dl" v-if="response" v-on:click="modello" rounded color="primary">
        <span >
            {{ $t("wgu-getPointCloud.model") }}
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
import OlPolygonSelection from './OlPolygonSelection.js';
import { WguEventBus } from '@/WguEventBus';
import axios from 'axios';

export default {
  name: 'wgu-getPointCloud-win',
  // make sure to register the 'Mapable' mixin
  mixins: [Mapable],
  inheritAttrs: false,
  components: {
    'wgu-module-card': ModuleCard
  },
  props: {
    icon: { type: String, required: false, default: 'star' },
    iconsOnly: { type: Boolean, required: false, default: false },
    selectType: { type: String, default: 'poly' }
  },
  // here we define variables that are used in the HTML above
  data () {
    return {
      selectTypeData: this.selectType,
      rawExtractionLayer: undefined,
      wkt: undefined,
      loading: false,
      response: undefined
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
      this.olMapCtrl = new OlPolygonSelection(this.map, 'EPSG:7792', parseInt(process.env.VUE_APP_MAX_CLOUD_POINTS) / 50) // , this.$attrs);
      this.olMapCtrl.createSelectionLayer();
      this.rawExtractionLayer = undefined;
    },
    /**
       * This function is executed, after the map is bound (see mixins/Mapable)
       */
    onMapUnbound () {
      console.log('onMapUnbound')
      if (this.olMapCtrl) {
        this.olMapCtrl.destroy();
        this.olMapCtrl = undefined;
        if (this.rawExtractionLayer) {
          this.map.removeLayer(this.rawExtractionLayer)
        }
      }
    },

    show (visible) {
      console.log('SHOW', this.map.getView().getZoom())
      if (!this.olMapCtrl) {
        return;
      }
      if (visible) {
        WguEventBus.$emit('wgu-start-menu-one-window', this.$refs.card.moduleName + '-win');
        this.olMapCtrl.addInteraction(this.selectTypeData, this.onEndSelect);
      } else {
        this.olMapCtrl.removeInteraction();
      }
    },

    download () {
      window.open(this.response.output_laz, '_blank');
    },

    modello () {
      window.open(this.response.output_dir + '/model/index.html', '_blank');
    },

    onEndSelect (wkt) {
      console.log('onEndSelect')
      // wrap geom into object, otherwise the injection into childs does
      // not work. Maybe the OL object does not feel changed for Vue
      console.log(wkt)
      const me = this
      me.wkt = wkt
      WguEventBus.$emit('app-loading-mask-toggle', true);
      const url = process.env.VUE_APP_LIDEX + '/punti/'
      axios.post(url, { extent: undefined, geom: me.wkt })
        .then(response => {
          console.log(response.data)
          me.response = response.data
          WguEventBus.$emit('app-loading-mask-toggle', false);
        }).catch(console.error)
    }

  }
};
</script>
<!-- Here we do the styling of our module -->
<style scoped>
/* our module has the class '.sample-module' and we reference it here */
.wgu-getPointCloud.wgu-floating {
  max-height: 500px;
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

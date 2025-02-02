<!-- The template contains the HTML of our module  -->
<template>
  <!--
  Our module builds upon the 'wgu-module-card'
  it handles the integration into Wegue
  like adding a button in the toolbar
  -->
  <wgu-module-card
    v-bind="$attrs"
    moduleName="wgu-start-menu"
    class="wgu-start-menu"
    :icon="icon"
    ref="card"
  >
    <!--
    Here goes the actual content of the module
    We use a the component 'v-card-text' from the Vuetify library
    -->
    <v-card-text>
    <v-container>
    <!-- slot to inject components before the auto-generated buttons (by config) -->
    <v-row><h3>{{ $t("wgu-start-menu.abstract") }}</h3></v-row>
    <v-list>
      <slot name="wgu-tb-before-auto-buttons"></slot>

      <template v-for="(tbButton, index) in tbButtons"  >
        <v-list-item
            :key="index">
          <component
            :is="tbButton.type"
            :key="index"
            v-bind="tbButton"
          />
        </v-list-item>
      </template>
    </v-list>
    <v-row>
      <v-spacer></v-spacer>
      <v-col md="1">
        <v-btn
          icon
          color="primary"
          @click="openLink()"
        >
          <v-icon dark>
            mdi-help-circle
          </v-icon>
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
    </v-card-text>
  </wgu-module-card>
</template>
<script>
// the module card is a the template for a typical Wegue module
import ModuleCard from '../../src/components/modulecore/ModuleCard';
import Vue from 'vue'
import ToggleButton from '../../src/components/modulecore/ToggleButton'
import printCloudModule from './lidex/getPointCloud'
import profili from './lidex/profili'
import { WguEventBus } from '@/WguEventBus';
import { Mapable } from '../../src/mixins/Mapable';
import axios from 'axios';

export default {
  name: 'wgu-start-menu-win',
  inheritAttrs: false,
  mixins: [Mapable],
  components: {
    'wgu-module-card': ModuleCard,
    'wgu-toggle-btn': ToggleButton,
    'wgu-getPointCloud-win': printCloudModule,
    'wgu-profili-win': profili
  },
  props: {
    icon: { type: String, required: false, default: 'star' },
    items: { type: Array, required: false }
  },
  // here we define variables that are used in the HTML above
  data () {
    return {
      tbButtons: this.getModuleButtons()
    };
  },
  computed: {
  },

  created () {
    WguEventBus.$on('wgu-start-menu-one-window', this.oneWindow);
  },

  mounted () {
    console.log('MOUNTED start menu', this.exclusions)
    const me = this
    const url = process.env.VUE_APP_LIDEX + 'coverage_extent/'
      axios.get(url)
        .then(response => {
          console.log(response)
          me.map.getView().fit(response.data.extent)
        }).catch(console.error)
  },

  methods: {
    /**
     * This function is called once the map is bound to the application
     */
    onMapBound () {
    },

    getMenuComponents (exclude) {
      const menuComponents = []
      const exclusions = ['wgu-module-card', 'wgu-toggle-btn', 'wgu-start-menu-win'];
      if (exclude) {
        exclusions.push(exclude)
      }
      Object.keys(this.$options.components).forEach(element => {
        if (!exclusions.includes(element) && this.items.includes(element.replace('-win', ''))) {
          menuComponents.push(element.replace('-win', ''))
        }
      });
      return menuComponents
    },

    oneWindow (excludedModule) {
      console.log('oneWindow', this.getMenuComponents(excludedModule))
      this.getMenuComponents(excludedModule).forEach(element => {
        console.log('oneWindow emit', element + '-visibility-change')
        WguEventBus.$emit(element + '-visibility-change', false);
      });
    },

    openLink () {
      window.open('/dbtman/doc/LEGGIMI.html', '_blank').focus()
    },

    /**
     * Determines the module button configuration objects from app-config:
     * If the module button toggles a window, then a generic wgu-toggle-btn will
     * be returned - otherwise the button is custom.
     *
     *    menuButtons: [
     *      {type: 'wgu-layerlist-toggle-btn'},
     *      {type: 'wgu-helpwin-toggle-btn'},
     *      {type: 'wgu-measuretool-toggle-btn'}
     *    ]
     * @param  {String} target Either 'menu' or 'toolbar'
     * @return {Array} module button configuration objects
     */
    getModuleButtons () {
      const buttonSet = this.getMenuComponents()
      const appConfig = Vue.prototype.$appConfig || {};
      const modulesConfs = appConfig.modules || {};
      const buttons = [];
      for (const key of Object.keys(modulesConfs)) {
        const moduleOpts = appConfig.modules[key];
        console.log(moduleOpts, this.$t(key + '.title'))
        moduleOpts.color = 'primary'
        if (buttonSet.includes(key)) {
          buttons.push({
            type: moduleOpts.win ? 'wgu-toggle-btn' : key + '-btn',
            moduleName: key,
            ...moduleOpts,
            color: 'primary',
            label: this.$t(key + '.title')
          });
        }
      }
      return buttons;
    },

    show (visible) {
      console.log('SHOW', this.$refs.card.moduleName)
      if (visible) {
        WguEventBus.$emit('wgu-start-menu-one-window', this.$refs.card.moduleName + '-win');
      }
    }

  }
};
</script>
<!-- Here we do the styling of our module -->
<style scoped>
/* our module has the class '.sample-module' and we reference it here */
.wgu-start-menu.wgu-floating {
  width: 500px;
}
</style>

<style scoped>
.v-btn-toggle-stacked {
  flex-direction: column;
  min-width: 100%;
}
.v-btn {
  width: 100% ! important;
}
</style>

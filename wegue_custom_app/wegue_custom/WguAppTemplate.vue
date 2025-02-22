<template>
  <v-app id="wgu-app" data-app :class="{ 'wgu-app': true, 'wgu-app-embedded': isEmbedded }">

    <slot name="wgu-app-begin" />

    <wgu-app-header>
      <!-- forward the slots of AppHeader -->
      <slot name="wgu-tb-start" slot="wgu-tb-start" />
      <slot name="wgu-tb-after-title" slot="wgu-tb-after-title" />
      <slot name="wgu-tb-before-auto-buttons" slot="wgu-tb-before-auto-buttons" />
      <slot name="wgu-tb-after-auto-buttons" slot="wgu-tb-after-auto-buttons" />
      <slot name="wgu-tb-end" slot="wgu-tb-end" />
    </wgu-app-header>

    <slot name="wgu-after-header" />

    <wgu-app-sidebar v-if="sidebarWins.length" v-bind="sidebarConfig">
        <template v-for="(moduleWin, index) in sidebarWins">
          <component
            :is="moduleWin.type" :key="index"
            v-bind="moduleWin"
          />
      </template>
    </wgu-app-sidebar>

    <slot name="wgu-before-content" />
    <v-main app>
      <v-container id="ol-map-container" fluid class="fill-height pa-0">
        <wgu-map />
        <!-- layer loading indicator -->
        <wgu-maploading-status />
        <slot name="wgu-after-map">
        </slot>
        <!-- Portal to overlay the map content from an application module -->
        <portal-target name="map-overlay" />
        <wgu-app-logo />
        <wgu-bglayerswitcher />
        <wgu-overviewmap v-if="overviewMapConfig" v-bind="overviewMapConfig"/>
        <!-- Register custom overlays, e.g. feature hover components here -->
        <wgu-hover-tooltip />
      </v-container>
    </v-main>

    <template v-for="(moduleWin, index) in floatingWins">
      <component
        :is="moduleWin.type" :key="index"
        v-bind="moduleWin"
      />
    </template>

    <slot name="wgu-before-footer" />

    <wgu-app-footer
      :footerTextLeft="$t('app.footerTextLeft')"
      :footerTextRight="$t('app.footerTextRight')"
      :showCopyrightYear="showCopyrightYear"
    />

    <slot name="wgu-after-footer" />

    <!-- app wide loading mask,
    use WguEventBus.$emit('app-loading-mask-toggle', newViz) to show/hide -->
    <wgu-app-loading-mask />

    <slot name="wgu-app-end" />

  </v-app>
</template>

<script>
import Vue from 'vue'
import { WguEventBus } from '../src/WguEventBus'
import OlMap from '../src/components/ol/Map'
import HoverTooltip from '../src/components/ol/HoverTooltip'
import AppHeader from './components/AppHeader'
import AppFooter from './components/AppFooter'
import AppSidebar from './components/AppSidebar'
import AppLogo from '../src/components/AppLogo'
import AppLoadingMask from '../src/components/AppLoadingMask'
import BgLayerSwitcher from '../src/components/bglayerswitcher/BgLayerSwitcher.vue'
import OverviewMap from '../src/components/overviewmap/OverviewMap.vue'
import MeasureWin from '../src/components/measuretool/MeasureWin'
import LayerListWin from '../src/components/layerlist/LayerListWin'
import HelpWin from '../src/components/helpwin/HelpWin'
import InfoClickWin from '../src/components/infoclick/InfoClickWin'
import MapLoadingStatus from '../src/components/progress/MapLoadingStatus'
import AttributeTableWin from '../src/components/attributeTable/AttributeTableWin.vue'
import MapRecorderWin from '../src/components/maprecorder/MapRecorderWin'
import printModule from './components/printDialog'
import printCloudModule from './components/lidex/getPointCloud'
import profili from './components/lidex/profili'
import dbtmanStart from './components/dbtmanStart.vue'

export default {
  name: 'wgu-app-tpl',
  components: {
    'wgu-map': OlMap,
    'wgu-hover-tooltip': HoverTooltip,
    'wgu-app-header': AppHeader,
    'wgu-app-footer': AppFooter,
    'wgu-app-sidebar': AppSidebar,
    'wgu-app-logo': AppLogo,
    'wgu-app-loading-mask': AppLoadingMask,
    'wgu-bglayerswitcher': BgLayerSwitcher,
    'wgu-overviewmap': OverviewMap,
    'wgu-measuretool-win': MeasureWin,
    'wgu-layerlist-win': LayerListWin,
    'wgu-helpwin-win': HelpWin,
    'wgu-infoclick-win': InfoClickWin,
    'wgu-maploading-status': MapLoadingStatus,
    'wgu-attributetable-win': AttributeTableWin,
    'wgu-maprecorder-win': MapRecorderWin,
    'wgu-print-win': printModule,
    'wgu-getPointCloud-win': printCloudModule,
    'wgu-profili-win': profili,
    'wgu-start-menu-win': dbtmanStart
  },
  data () {
    return {
      isEmbedded: false,
      sidebarConfig: this.getSidebarConfig(),
      overviewMapConfig: this.getOverviewMapConfig(),
      floatingWins: this.getModuleWinData('floating'),
      sidebarWins: this.getModuleWinData('sidebar'),
      showCopyrightYear: Vue.prototype.$appConfig.showCopyrightYear
    }
  },
  created () {
    this.setDocumentTitle();
  },
  mounted () {
    // apply the isEmbedded state to the member var
    this.isEmbedded = this.$isEmbedded;

    // make the refs (floating module window, which are not connected to their
    // related components, e.g. buttons to toggle them)
    const refs = this.$refs;
    const cmpLookup = {};
    for (const key of Object.keys(refs)) {
      cmpLookup[key] = refs[key][0];
    }
    Vue.prototype.cmpLookup = cmpLookup;
    // inform registered cmps that the app is mounted and the dynamic
    // components are available
    WguEventBus.$emit('app-mounted');
  },
  methods: {
    /**
       * Returns the configuration object for the sidebar from app-config.
       * @return {Object} Sidebar configuration object.
       */
    getSidebarConfig () {
      const appConfig = Vue.prototype.$appConfig || {};
      return appConfig.sidebar;
    },
    /**
       * Returns the configuration object for the overview map from app-config.
       * @return {Object} Overview map configuration object.
       */
    getOverviewMapConfig () {
      const appConfig = Vue.prototype.$appConfig || {};
      return appConfig.overviewMap;
    },
    /**
       * Determines the module window configuration objects from app-config:
       *     moduleWins: [
       *       {type: 'wgu-layerlist-win'},
       *       {type: 'wgu-measuretool-win'}
       *     ]
       * @param  {String} target Either 'floating' or 'sidebar'
       * @return {Array} module window configuration objects
       */
    getModuleWinData (target) {
      const appConfig = Vue.prototype.$appConfig || {};
      const modulesConfs = appConfig.modules || {};
      const moduleWins = [];
      for (const key of Object.keys(modulesConfs)) {
        const moduleOpts = appConfig.modules[key];
        if (moduleOpts.win === target) {
          moduleWins.push({
            type: key + '-win',
            ...moduleOpts
          });
        }
      }
      return moduleWins;
    },
    /**
       * Sets the document title from language file.
       */
    setDocumentTitle () {
      document.title = this.$t('app.browserTitle') || document.title;
    }
  },
  watch: {
    /**
       * Watch for locale changes.
       */
    '$i18n.locale': function () {
      this.setDocumentTitle();
    }
  }
}
</script>

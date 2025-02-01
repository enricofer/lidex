import DrawInteraction from 'ol/interaction/Draw';
import DragBox from 'ol/interaction/DragBox';
import { unByKey } from 'ol/Observable.js';
import VectorSource from 'ol/source/Vector';
import VectorLayer from 'ol/layer/Vector';
import Style from 'ol/style/Style';
import Stroke from 'ol/style/Stroke';
import Circle from 'ol/style/Circle';
import Fill from 'ol/style/Fill';
import WKT from 'ol/format/WKT';
import Polygon from 'ol/geom/Polygon';
import LineString from 'ol/geom/LineString';

/**
 * Class holding the OpenLayers related logic for the measure tool.
 */
export default class OlPolygonSelection {
  /* the OL map we want to measure on */
  map = null;

  constructor (olMap, targetProjection, overflowArea) {
    this.map = olMap;
    this.targetProjection = targetProjection
    this.selectionLayer = undefined;
    this.controlGeom = undefined;
    this.overflowArea = overflowArea
    this.overflow = false
  }

  /**
   * Tears down this controller.
   */
  destroy () {
    console.log('destroy')
    if (!this.selectionLayer || !this.map) {
      return;
    }
    this.removeInteraction();
    this.map.removeLayer(this.selectionLayer);
    this.selectionLayer = undefined;
  }

  /**
   * Creates a vector layer for the measurement results and adds it to the
   * map.
   */
  createSelectionLayer () {
    console.log('createSelectionLayer')
    const me = this;
    // create a vector layer to
    const source = new VectorSource();
    this.selectionLayer = new VectorLayer({
      lid: 'wgu-selection-layer',
      displayInLayerList: false,
      source,
      style: new Style({
        fill: new Fill({
          color: 'rgba(255, 255, 255, 0.2)' // measureConf.fillColor ||
        }),
        stroke: new Stroke({
          color: 'rgba(0, 255, 255, 0.7)', // measureConf.strokeColor ||
          width: 2
        })
      })
    });

    me.map.addLayer(this.selectionLayer);

    // make vector source available as member
    me.source = source;
  }

  /**
   * Creates and adds the necessary draw interaction and adds it to the map.
   */
  addInteraction (selectType, mapEndSelect) {
    console.log('addInteraction', selectType)
    const me = this;
    // cleanup possible old draw interaction
    if (me.draw) {
      me.removeInteraction();
    }
    let draw

    const reprojectionOptions = {
      dataProjection: this.targetProjection ? this.targetProjection : this.map.getView().getProjection(),
      featureProjection: this.map.getView().getProjection()
    }

    if (selectType === 'poly') {
      draw = new DrawInteraction({
        source: me.source,
        type: 'Polygon',
        maxPoints: undefined,
        style: function (feature, resolution) {
          return new Style({
            fill: new Fill({
              color: 'rgba(255, 255, 255, 0.2)'
            }),
            stroke: new Stroke({
              color: me.overflow ? 'rgba(255, 0, 0, 0.7)' : 'rgba(0, 255, 255, 0.7)',
              lineDash: [10, 10],
              width: 3
            }),
            image: new Circle({
              radius: 5,
              stroke: new Stroke({
                color: 'rgba(0, 255, 255, 0.7)'
              }),
              fill: new Fill({
                color: 'rgba(255, 255, 255, 0.2)'
              })
            })
          })
        },
        geometryFunction: function (coordinates, geometry) {
          // coordinates.push(coordinates[0])
          // if ( coordinates[0][0][0] !== coordinates[0][coordinates.length][0] ) {
          //  coordinates[0].push(coordinates[0][0])
          // }
          if (coordinates[0].length > 2) {
            const controlCoords = JSON.parse(JSON.stringify(coordinates))
            if (controlCoords[0][0][0] !== controlCoords[0][controlCoords.length][0]) {
              controlCoords[0].push(controlCoords[0][0])
            }
            me.controlGeom = new Polygon(controlCoords, 'XY')
            // controlGeom.setCoordinates(controlCoords)
            const area = me.controlGeom.getArea()
            if (me.overflowArea && area > me.overflowArea) {
              me.overflow = true
            } else {
              me.overflow = false
            }
          }

          if (coordinates && !geometry) {
            geometry = new LineString(coordinates);
          }
          console.info(coordinates);

          return geometry
        }
      });
      // preserve measure type to re-use in draw events

      let listener;
      // eslint-disable-next-line
      let sketch;
      draw.on('drawstart', (evt) => {
        // clear old measure features
        me.source.clear();
        // preserve sketch
        sketch = evt.feature;

        listener = me.map.on('click', (evt) => {
          // const geom = sketch.getGeometry();
          // execute given callback
        });
      }, me);

      draw.on('drawend', () => {
        console.log('drawend')
        // const linestringGeom = sketch.getGeometry();
        // const geom = new Polygon((linestringGeom.getCoordinates()))
        const geom = me.controlGeom
        const converter = new WKT()
        console.log('REPRO1', this.targetProjection, reprojectionOptions, this.targetProjection ? reprojectionOptions : {})
        if (!me.overflow) mapEndSelect(converter.writeGeometry(geom, this.targetProjection ? reprojectionOptions : {}))
        // unset sketch
        sketch = null;
        unByKey(listener);
      }, me);
    } else if (selectType === 'box') {
      draw = new DragBox({ className: 'myDragBox' })

      draw.on('boxdrag', function () {
        const extent = draw.getGeometry().getExtent();
        const area = Math.abs(extent[2] - extent[0]) * Math.abs(extent[3] - extent[1])
        if (me.overflowArea && area > me.overflowArea) {
          me.overflow = true
          document.getElementsByClassName('myDragBox')[0].style.border = '3px dashed rgba(255, 0, 0, 0.7)'
        } else {
          me.overflow = false
          document.getElementsByClassName('myDragBox')[0].style.border = '3px dashed rgba(0, 255, 255, 0.7)'
        }
      })

      draw.on('boxend', (evt) => {
        console.log(evt)
        const geom = draw.getGeometry();
        const converter = new WKT()
        console.log('REPRO2', this.targetProjection, reprojectionOptions, this.targetProjection ? reprojectionOptions : {})
        if (!me.overflow) mapEndSelect(converter.writeGeometry(geom, this.targetProjection ? reprojectionOptions : {}))
      })
    }

    me.map.addInteraction(draw);
    // make draw interaction available as member
    me.draw = draw;
  }

  /**
   * Removes the current interaction and clears the values.
   */
  removeInteraction () {
    console.log('removeInteraction')
    if (this.draw) {
      this.map.removeInteraction(this.draw);
      this.draw = undefined;
    }
    if (this.source) {
      this.source.clear();
    }
  }
}

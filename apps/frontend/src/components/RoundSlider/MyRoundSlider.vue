<script setup lang="ts">
import { onMounted, ref } from 'vue';
import $ from 'jquery';
import 'round-slider';

const randomRoundSliderId = ref(String(Math.random()).replace('.', ''));
const randomRoundSliderInputId = ref(String(Math.random()).replace('.', ''));

const props = defineProps<{
  min: number;
  step: number;
  max: number;
}>();

const model = defineModel();

onMounted(() => {

  const id = '#' + randomRoundSliderId.value;
  const idInput = '#' + randomRoundSliderInputId.value;
  
  $(id).roundSlider({
    width: 6,
    radius: 24,
    handleSize: 10,
    sliderType: 'min-range',
    value: model.value,
    startAngle: 315,
    endAngle: 225,
    step: 1,
    min: props.min,
    max: props.max,
    editableTooltip: true,
    
    stop: (e) => {
      console.log('stop', e);
      model.value = e.value;
    },
    change: (e) => {
      console.log('change', e);
      model.value = e.value;
    },
  });


});
</script>

<template>
  <div :id="randomRoundSliderId"></div>
</template>

<style>
.rs-ie,
.rs-edge,
.rs-handle {
  -ms-touch-action: none;
  touch-action: none;
}
.rs-control {
  position: relative;
  outline: 0 none;
}
.rs-container {
  position: relative;
}
.rs-control *,
.rs-control *:before,
.rs-control *:after {
  -webkit-box-sizing: border-box;
  box-sizing: border-box;
}
.rs-animation .rs-transition {
  transition: all 0.5s linear 0s;
}
.rs-bar {
  -webkit-transform-origin: 100% 50%;
  -ms-transform-origin: 100% 50%;
  transform-origin: 100% 50%;
}
.rs-control .rs-split .rs-path,
.rs-control .rs-overlay1,
.rs-control .rs-overlay2 {
  -webkit-transform-origin: 50% 100%;
  -ms-transform-origin: 50% 100%;
  transform-origin: 50% 100%;
}
.rs-control .rs-overlay {
  -webkit-transform-origin: 100% 100%;
  -ms-transform-origin: 100% 100%;
  transform-origin: 100% 100%;
}
.rs-rounded .rs-seperator,
.rs-split .rs-path {
  -webkit-background-clip: padding-box;
  background-clip: padding-box;
}
.rs-disabled {
  opacity: 0.35;
}
.rs-inner-container {
  height: 100%;
  width: 100%;
  position: absolute;
  top: 0;
  overflow: hidden;
}
.rs-control .rs-quarter div.rs-block {
  height: 200%;
  width: 200%;
}
.rs-control .rs-half.rs-top div.rs-block,
.rs-control .rs-half.rs-bottom div.rs-block {
  height: 200%;
  width: 100%;
}
.rs-control .rs-half.rs-left div.rs-block,
.rs-control .rs-half.rs-right div.rs-block {
  height: 100%;
  width: 200%;
}
.rs-control .rs-bottom .rs-block {
  top: auto;
  bottom: 0;
}
.rs-control .rs-right .rs-block {
  right: 0;
}
.rs-block.rs-outer {
  border-radius: 1000px;
}
.rs-block {
  height: 100%;
  width: 100%;
  display: block;
  position: absolute;
  top: 0;
  overflow: hidden;
  z-index: 3;
}
.rs-block .rs-inner {
  border-radius: 1000px;
  display: block;
  height: 100%;
  width: 100%;
  position: relative;
}
.rs-overlay {
  width: 50%;
}
.rs-overlay1,
.rs-overlay2 {
  width: 100%;
}
.rs-overlay,
.rs-overlay1,
.rs-overlay2 {
  position: absolute;
  background-color: #fff;
  z-index: 3;
  top: 0;
  height: 50%;
}
.rs-bar {
  display: block;
  position: absolute;
  bottom: 0;
  height: 0;
  z-index: 10;
}
.rs-bar.rs-rounded {
  z-index: 5;
}
.rs-bar .rs-seperator {
  height: 0;
  display: block;
  float: left;
}
.rs-bar:not(.rs-rounded) .rs-seperator {
  border-left: none;
  border-right: none;
}
.rs-bar.rs-start .rs-seperator {
  border-top: none;
}
.rs-bar.rs-end .rs-seperator {
  border-bottom: none;
}
.rs-bar.rs-start.rs-rounded .rs-seperator {
  border-radius: 0 0 1000px 1000px;
}
.rs-bar.rs-end.rs-rounded .rs-seperator {
  border-radius: 1000px 1000px 0 0;
}
.rs-full .rs-bar,
.rs-half .rs-bar {
  width: 50%;
}
.rs-half.rs-left .rs-bar,
.rs-half.rs-right .rs-bar,
.rs-quarter .rs-bar {
  width: 100%;
}
.rs-full .rs-bar,
.rs-half.rs-left .rs-bar,
.rs-half.rs-right .rs-bar {
  top: 50%;
}
.rs-bottom .rs-bar {
  top: 0;
}
.rs-half.rs-right .rs-bar,
.rs-quarter.rs-right .rs-bar {
  right: 100%;
}
.rs-handle.rs-move {
  cursor: move;
}
.rs-readonly .rs-handle.rs-move {
  cursor: default;
}
.rs-classic-mode .rs-path {
  display: block;
  height: 100%;
  width: 100%;
}
.rs-split .rs-path {
  border-radius: 1000px 1000px 0 0;
  overflow: hidden;
  height: 50%;
  position: absolute;
  top: 0;
  z-index: 2;
}
.rs-control .rs-svg-container {
  display: block;
  position: absolute;
  top: 0;
}
.rs-control .rs-bottom .rs-svg-container {
  top: auto;
  bottom: 0;
}
.rs-control .rs-right .rs-svg-container {
  right: 0;
}
.rs-tooltip {
  position: absolute;
  cursor: default;
  border: 1px solid transparent;
  z-index: 10;
}
.rs-full .rs-tooltip {
  top: 50%;
  left: 50%;
}
.rs-bottom .rs-tooltip {
  top: 0;
}
.rs-top .rs-tooltip {
  bottom: 0;
}
.rs-right .rs-tooltip {
  left: 0;
}
.rs-left .rs-tooltip {
  right: 0;
}
.rs-half.rs-top .rs-tooltip,
.rs-half.rs-bottom .rs-tooltip {
  left: 50%;
}
.rs-half.rs-left .rs-tooltip,
.rs-half.rs-right .rs-tooltip {
  top: 50%;
}
.rs-tooltip .rs-input {
  display: inline;
  outline: 0 none;
  border: none; 
}
.rs-tooltip-text {
  font-family: verdana;
  font-size: 11px;
  border-radius: 7px;
  text-align: center;
  color: inherit;
}
.rs-tooltip.rs-edit {
  padding: 5px 8px;
}
.rs-tooltip.rs-hover,
.rs-tooltip.rs-edit:hover {
  border: 1px solid #aaa;
  cursor: pointer;
}
.rs-readonly .rs-tooltip.rs-edit:hover {
  border-color: transparent;
  cursor: default;
}
.rs-tooltip.rs-center {
  margin: 0 !important;
}
.rs-half.rs-top .rs-tooltip.rs-center,
.rs-half.rs-bottom .rs-tooltip.rs-center {
  transform: translate(-50%, 0);
}
.rs-half.rs-left .rs-tooltip.rs-center,
.rs-half.rs-right .rs-tooltip.rs-center {
  transform: translate(0, -50%);
}
.rs-full .rs-tooltip.rs-center {
  transform: translate(-50%, -50%);
}
.rs-tooltip.rs-reset {
  margin: 0 !important;
  top: 0 !important;
  left: 0 !important;
}
.rs-handle {
  border-radius: 1000px;
  outline: 0 none;
  float: left;
}
.rs-handle.rs-handle-square {
  border-radius: 0;
}
.rs-handle-dot {
  border: 1px solid #aaa;
  padding: 6px;
}
.rs-handle-dot:after {
  display: block;
  content: '';
  border: 1px solid #aaa;
  height: 100%;
  width: 100%;
  border-radius: 1000px;
}
.rs-seperator {
  border: 1px solid #aaa;
}
.rs-border {
  border: 1px solid #aaa;
}
.rs-path-color {
  background-color: #fff;
}
.rs-range-color {
  background-color: #54bbe0;
}
.rs-bg-color {
  background-color: #fff;
}
.rs-handle {
  background-color: #838383;
}
.rs-handle-dot {
  background-color: #fff;
}
.rs-handle-dot:after {
  background-color: #838383;
}
.rs-path-inherited .rs-path {
  opacity: 0.2;
}
.rs-svg-mode .rs-path {
  stroke: #fff;
}
.rs-svg-mode .rs-range {
  stroke: #54bbe0;
}
.rs-svg-mode .rs-border {
  stroke: #aaa;
}
.rs-handle {
  background-color: #f3f3f3;
  box-shadow: 0px 0px 4px 0px #000;
}
.rs-tooltip-text {
  font-size: 11px;
  font-weight: 500;
  font-family: Avenir, Tahoma, Verdana, sans-serif;
}
.rs-animation .rs-transition {
  transition: all 0.5s ease-in-out 0s;
}
.rs-tooltip.rs-hover,
.rs-tooltip.rs-edit:hover {
  border: 1px solid #cacaca;
}
.rs-handle {
  background-color: #f3f3f3;
  box-shadow: 0px 0px 4px 0px #000;
}

.rs-tooltip-text {
  font-size: 11px;
  font-weight: 300;
  font-family: Avenir, Tahoma, Verdana, sans-serif;
}

.rs-animation .rs-transition {
  transition: all 0.5s ease-in-out 0s;
}

.rs-tooltip.rs-hover,
.rs-tooltip.rs-edit:hover {
  border: 1px solid #cacaca;
}
</style>

<template>
  <div class="section">
    <slot></slot>
  </div>
</template>

<style>
.section {
  padding: 10px;
  margin: 30px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.07), 0 2px 4px rgba(0, 0, 0, 0.07),
    0 4px 8px rgba(0, 0, 0, 0.07), 0 8px 16px rgba(0, 0, 0, 0.07), 0 16px 32px rgba(0, 0, 0, 0.07),
    0 32px 64px rgba(0, 0, 0, 0.07);
  background-color: #f1f2f8;
}
</style>

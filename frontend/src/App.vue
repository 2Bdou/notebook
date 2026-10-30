<template>
  <router-view />
</template>

<script setup lang="ts">
// 根组件：仅承载路由出口，全局样式在此声明
</script>

<style>
/* 全局重置样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body,
#app {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
    'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: #333;
  background: #f5f5f5;
}

button {
  cursor: pointer;
  border: none;
  background: none;
  font-size: inherit;
}

input {
  outline: none;
}

a {
  text-decoration: none;
  color: inherit;
}
</style>

<template>
  <nav class="navbar bg-body-tertiary">
    <div class="container">
      <router-link to="/">ai.m16.tech</router-link>
    </div>
  </nav>
  <div class="content">
    <router-view />
  </div>
</template>

<style scoped="scoped">
.content {
  margin: auto;
  margin-top: 50px;
  text-align: center;
  width: 1200px;
}
</style>

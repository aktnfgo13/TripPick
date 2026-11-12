import {createApp} from 'vue'
import App from './App.vue'

createApp(App).mount('#app')

window.addEventListener('hashchange', () => {
  if (location.hash) location.reload()
})

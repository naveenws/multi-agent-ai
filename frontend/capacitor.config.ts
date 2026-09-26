import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.naveen.multiagentai',
  appName: 'Multi-Agent AI',
  webDir: 'dist',
  plugins: {
    CapacitorHttp: {
      enabled: true,
    }
  }
};

export default config;

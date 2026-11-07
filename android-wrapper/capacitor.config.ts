import type { CapacitorConfig } from '@capacitor/cli';
// Replace with the HTTPS URL of your deployed Flask application.
const config: CapacitorConfig = {
  appId: 'com.ntb.monitoring',
  appName: 'Narcotics Traffic Buster',
  webDir: 'www',
  server: { url: 'https://REPLACE-WITH-YOUR-DEPLOYED-DOMAIN', cleartext: false, androidScheme: 'https' },
  plugins: { SplashScreen: { launchShowDuration: 1200, backgroundColor: '#0b1422' } }
};
export default config;

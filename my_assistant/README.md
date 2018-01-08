# My Assistant
## To run
* Make sure your virtualenv is up and running and you have all the latest depedencies
1. Serve up: ngrok http 5000
2. Run: python webhook.py
3. In Api.ai, make sure the webhook URL in the Fulfillment section matches the secure URL from ngrok
4. Navigate to https://console.actions.google.com and find the HelloWorld project to test locally
5. Test locally by entering text commands into the web tool or via your Google Home
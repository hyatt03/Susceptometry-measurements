(function() {
    console.log("Script Injected");
    // define monkey patch function
    const monkeyPatch = () => {
      let oldXHROpen = window.XMLHttpRequest.prototype.open;
      window.XMLHttpRequest.prototype.open = function() {
        this.addEventListener("load", function() {
          const responseBody = this.responseText;
          console.log(`Response Body: ${responseBody}`, this);
          document.getElementById('myDataHolder').setAttribute('myData', responseBody)
        });
        return oldXHROpen.apply(this, arguments);
      };
    };

    monkeyPatch();
})();

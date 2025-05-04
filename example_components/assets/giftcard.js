/**
 * Gift Card Template Script
 * ------------------------------------------------------------------------------
 * A file that contains scripts highly couple code to the Gift Card template.
 */

(function() {
  var config = {
    qrCode: '#QrCode',
    giftCardCode: '.giftcard__code'
  };

  // init QR code
  const qrCode = document.querySelector(config.qrCode);
  if (qrCode) {
    const qrCodeText = qrCode.getAttribute('data-identifier');
    new QRCode(qrCode, {
      text: qrCodeText,
      width: 120,
      height: 120
    });
  }

  const giftCardCode = document.querySelector(config.giftCardCode);
  if (giftCardCode) {
    // Auto-select gift card code on click, based on ID passed to the function
    function selectText(evt) {
      var text = document.querySelector('#GiftCardDigits');
      var range = '';

      if (document.body.createTextRange) {
        range = document.body.createTextRange();
        range.moveToElementText(text);
        range.select();
      } else if (window.getSelection) {
        var selection = window.getSelection();
        range = document.createRange();
        range.selectNodeContents(text);
        selection.removeAllRanges();
        selection.addRange(range);
      }
    }
    giftCardCode.addEventListener('click', selectText())
  }
})();

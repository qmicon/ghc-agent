(function($) {
  'use strict';

  jQuery(document).ready(function($) {

   
    
    /*currency*/
    function convert_currency(value){
      var newCurrency = Currency.currentCurrency;
      var oldCurrency = shopCurrency;
      if(isNaN(value)){
        value =  0.0;
      }

      var cents = 0.0;
      var oldFormat = Currency.moneyFormats['USD'][ Currency.format] || '';
                                            var newFormat = Currency.moneyFormats[newCurrency][Currency.format] || '';
                                            if (oldFormat.indexOf('amount_no_decimals') !== -1) {
                                              cents = Currency.convert(parseInt(value, 10)*100, oldCurrency, newCurrency);
                                            }
      else if (oldCurrency === 'JOD' || oldCurrency == 'KWD' || oldCurrency == 'BHD') {
        cents = Currency.convert(parseInt(value, 10)/10, oldCurrency, newCurrency);
      }
      else { 
        cents = Currency.convert(parseInt(value, 10), oldCurrency, newCurrency);
      }
      var my_data =  Currency.formatMoney(cents, newFormat);
      return my_data;
      
      
    }
    /* end currency */

  

    /* Compare Product*/
    var storage = $.localStorage;
    var compare = {};
    var total_compare = 8;
    if (storage.isSet('compare')) {
      compare = storage.get('compare');
    } else {
      storage.set('compare', {});
    }
    function compare_to_table(data) {
      if (Object.keys(data).length <= 0) {
        return '';
      }
      var html = '';
      var i = 0;

      var end_check = (Object.keys(data).length - 1);
      var width_tr = (end_check > 0) ? (90 / (Object.keys(data).length)) : 90;
      var data_html = '';
      for (i = 0; i <= end_check; i++) {
        var el = data[i];
        var is_sale = false;
        if (el.compare_at_price > el.price) {
          is_sale = true
        }
        data_html = data_html + '<th class=" ' + el.handle + '"><button type="button" class="close remove-compare center-block" aria-label="Close" data-handle="' + el.handle + '">Remove<span aria-hidden="true" class="remove-compare-x">&times;</span></button></th>';
        //Start title 
        if (i == 0) {
          html = html + '<tr>';
          html = html + '<th width="15%" class="product-name" > Product name </th>';
        }
        html = html + '<td width="' + width_tr + '%"  class="' + el.handle + '"> ' + el.title + '  </td>';
        if (i >= end_check) {
          html = html + '</tr>';
        }
        // End Title 
      }
      for (i = 0; i <= end_check; i++) {
        var el = data[i];
        var is_sale = false;
        if (el.compare_at_price > el.price) {
          is_sale = true
        }
        if (i == 0) {
          html = html + '<tr>';
          html = html + '<th width="15%" class="product-name" > Product image </th>';

        }
        // start product image
        html = html + '<td width="' + width_tr + '%" class="item-row ' + el.handle + '" id="product-'+el.variants[0].id+'"> <img src="' + el.featured_image + '"  width="150"/> ' + '<div class="product-price"> ';
        if (is_sale) {
          html = html + '<strong>On Sale</strong>' + '<span class="price-sale"><span class="money" data-currency-'+Currency.currentCurrency+'="'+convert_currency(el.price,'11')+'">'+convert_currency(el.price,'11')+'</span></span>';
        } else {
          html = html + '<span class="price-sale"><span class="money" data-currency-'+Currency.currentCurrency+'="'+convert_currency(el.price,'11')+'">'+convert_currency(el.price,'11')+'</span></span>';
        }
        if (convert_currency(el.compare_at_price, 'nosymbol') > 0) {
          html = html + '<span class="visually-hidden">Regular price</span> <s>' + convert_currency(el.compare_at_price, '11') + '</s>';
        }
        html = html + '</div>';
        //convert_currency(el.price,'3');
        if (el.variants.length > 1) {
          html = html + '<a href="#" onclick="location.href=\'/products/' + el.handle + '\'">Select Options</a>';
        } else {
          html = html + '<form  action="/cart/add" method="post" class="variants clearfix" id="cart-form-'  + el.variants[0].id  + '">';
          html = html + '<a href="#" title="Add to Cart" data-pid="' + el.variants[0].id + '" class="add-cart-btn add-to-cart">Add to Cart</a>';
          html = html + '</form>';
        }
        html = html + ' </td>';

        if (i >= end_check) {
          html = html + '</tr>';
        }
        // End product image
      }
      for (i = 0; i <= end_check; i++) {
        var el = data[i];
        var is_sale = false;
        if (el.compare_at_price > el.price) {
          is_sale = true
        }
        if (i == 0) {
          html = html + '<tr>';
          html = html + '<th width="15%" class="product-name" > Product description </th>';

        }        
        html = html + '<td width="' + width_tr + '%" class="' + el.handle + ' "> <p class="description-compare"> ' + el.description.replace(/(<([^>]+)>)/ig, "").split(" ").splice(0, 40).join(" ") + "..." + ' </p> </td>';
        if (i >= end_check) {
          html = html + '<tr>';
        }

      }
      for (i = 0; i <= end_check; i++) {
        var el = data[i];
        var is_sale = false;
        if (el.compare_at_price > el.price) {
          is_sale = true
        }
        if (i == 0) {
          html = html + '<tr>';
          html = html + '<th width="15%" class="product-name" > AVAILABILITY </th>';

        }

        var avai_stock = (el.available) ? 'Available In stock' : 'Unavailable In stock';
        html = html + '<td   width="' + width_tr + '%" class="available-stock ' + el.handle + '"> <p> ' + avai_stock + ' </p> </td>';
        if (i >= end_check) {
          html = html + '<tr>';
        }

      }
      $(".th-compare").html('<td>Action</td>'+data_html);
      $("#table-compare").html(html);
    }
    function modal_compare(){
      if (!$.isEmptyObject(compare)) {
        // $(".error-compare").hide(20);
        var list_id = '';
        var json_compare = [];
        var check_end = 0;
        var compare_size = (Object.keys(compare).length - 1);
        $.each(compare, function(index, el) {
          var json_url = "/products/" + el + ".js";
          if ($.trim(el) != "") {
            jQuery.getJSON(json_url, function(product) {
              json_compare[check_end] = product;
              if (check_end >= compare_size) {
                compare_to_table(json_compare);
              }
              check_end += 1;
            });

          }

        });
        $("#moda-compare").fadeIn();
      }

    }
    $(document).on('click','.compare', function(event) {

      event.preventDefault();
      $(".loading-modal").fadeIn();
      /* Act on the event */
      var $this = $(this);
      var pid = $(this).data('pid');

      compare = storage.get('compare');

      if ($.isEmptyObject(compare)) {
        compare = {};
      }
      var check_compare = true;
      if (Object.keys(compare).length >= total_compare) {
        swal({
          title: "info",
          text: "Product Added over 8 product !. Do you want to compare 8 added product ?",
          type: "warning",
          showCancelButton: true,
          confirmButtonColor: "#4cae4c",
          confirmButtonText: "Yes,I want view it!",
          timer: 3000,
          cancelButtonText: "Continue",
          closeOnConfirm: true
        },
             function() {
          
               modal_compare(compare);
            
        });
      } else {
        for (var i = 1; i <= 8; i++) {
          if (compare['p' + i] == "" || compare['p' + i] == undefined) {
            compare['p' + i] = pid;
            break;
          } else if (compare['p' + i] == pid) {
            $this.addClass('added');
            check_compare = false;
            modal_compare(compare);

            break;
          }
        }
        if (check_compare) {
          storage.set('compare', compare);
          modal_compare(compare);
          $this.addClass('add-success');
          $("[data-pid='"+pid+"']").addClass('added').text('Added to compare');
        }
      }
      $(".loading-modal").hide(500);
    });

    $(document).on('click', '.remove-compare', function(event) {
      event.preventDefault();
      /* Act on the event */

      var id = $(this).data('handle');
      $("." + id).fadeOut(600).remove();
      $("[data-pid='"+id+"']").removeClass('added add-success').text('add to compare');
      $.each(compare, function(index, el) {
        if (el == id) {
          compare[index] = "";
          delete compare[index];
        }
      });
      storage.set('compare', compare);
     
    });

    /** End compare */


    if (!$.isEmptyObject(compare)) {
      $(".error-compare").hide(20);
      var list_id = '';
      var json_compare = [];
      var check_end = 0;
      var compare_size = (Object.keys(compare).length - 1);
      $.each(compare, function(index, el) {
        $("[data-pid='"+el+"']").addClass('added').text('Added to compare');
        var json_url = "/products/" + el + ".js";
        if ($.trim(el) != "") {
          jQuery.getJSON(json_url, function(product) {
            json_compare[check_end] = product;
            if (check_end >= compare_size) {
              compare_to_table(json_compare);
            }
            check_end += 1;
          });

        }

      });
    } else {
      $(".error-compare").fadeIn();
    }
	    

  });
})(jQuery);
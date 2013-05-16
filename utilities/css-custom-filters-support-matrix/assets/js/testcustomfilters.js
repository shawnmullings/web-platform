/*
Copyright (C) 2013 Adobe Systems, Incorporated. All rights reserved.

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/
$(function () {

    function removeBaseURL(src) {
        var urlRegexp = /url\(([^\)]*)\)/g;
        return src.replace(urlRegexp, function(match, url) {
            return "url(" + url.substr(url.lastIndexOf("/") + 1) + ")";
        });
    }

    var $div;
    var filterProperty = "filter"; // Fallback value

    function setup() {
        var prefixedProperties = ['-webkit-filter', '-ms-filter', '-o-filter', '-moz-filter'];
        var customFilterValue = 'custom(none mix(url(http://www.example.com/) normal source-atop), 10 20)';
        $div = $('<div></div>').appendTo($('body'));

        for (var i = 0; i < prefixedProperties.length; ++i) {
            $div.css(prefixedProperties[i], customFilterValue);
            if ($div.css(prefixedProperties[i]) == customFilterValue)
                filterProperty = prefixedProperties[i];
        }
    }

    function teardown() {
        $div.css(filterProperty, "");
    }


    function testCustomFiltersInline() {
        module('CSS Custom Filters', { 'setup': setup, 'teardown': teardown });

        test('Inline Syntax', function() {
            equal($div.css(filterProperty), 'custom(none mix(url(http://www.example.com/) normal source-atop), 10 20)', 'Minimal shader with geometry is not supported');

            var filterValue = 'custom(none url(http://www.example.com/), 1 1)';
            $div.css(filterProperty, filterValue);
            equal($div.css(filterProperty), filterValue, 'Minimal shader with no mix is not supported');

            filterValue = 'custom(none mix(url(http://www.example.com/) normal source-atop), 1 1, testArray array(1, 2, 3))';
            $div.css(filterProperty, filterValue);
            equal($div.css(filterProperty), filterValue, 'Array not supported');

            filterValue = 'custom(none mix(url(http://www.example.com/) color source-atop), 1 1)';
            $div.css(filterProperty, filterValue);
            equal($div.css(filterProperty), filterValue, 'Color blend-mode is not supported');


            filterValue = 'custom(none mix(url(http://www.example.com/) hue source-atop), 1 1)';
            $div.css(filterProperty, filterValue);
            equal($div.css(filterProperty), filterValue, 'Hue blend-mode is not supported');

            filterValue = 'custom(none mix(url(http://www.example.com/) saturation source-atop), 1 1)';
            $div.css(filterProperty, filterValue);
            equal($div.css(filterProperty), filterValue, 'Saturation blend-mode is not supported');

            filterValue = 'custom(none mix(url(http://www.example.com/) luminosity source-atop), 1 1)';
            $div.css(filterProperty, filterValue);
            equal($div.css(filterProperty), filterValue, 'Luminosity blend-mode is not supported');
        })

//        var filterValue = 'custom(none mix(url(http://www.example.com/) normal source-atop), 1 1, testArray array(1.0, 2.0, 3.0))';
//        $div.css(filterProperty, filterValue);

//        test('Array', function() {
//            equal($div.css(filterProperty), filterValue, 'Array not supported');
//        })
    }

//    function testCustomFiltersAtRule() {
//        module('CSS Custom Filters - @filter syntax', { 'setup': setup });
//
        // There's no real need to use a new setup method here.
//        test('Syntax', function() {
//            var filterRuleString = "@" + filterProperty + " test-filter {}";
//            var docStyleSheets = document.styleSheets;
//            var lastStyleSheet = docStyleSheets.length - 1;
//            var lastCssRule = docStyleSheets.item(lastStyleSheet).cssRules.length - 1;
//            var refSheet = docStyleSheets.item(lastStyleSheet);
//
//            test('@filter syntax', function() {
//                equal(refSheet.insertRule(filterRuleString, lastCssRule), lastCssRule, 'Simple @filter');
//            })
//        })
//    }

    testCustomFiltersInline();
    //testCustomFiltersAtRule();
})   

! function(t) {
    var e = {
            topSpacing: 0,
            bottomSpacing: 0,
            className: "is-sticky",
            wrapperClassName: "sticky-wrapper",
            center: !1,
            getWidthFrom: ""
        },
        n = t(window),
        i = t(document),
        a = [],
        s = n.height(),
        r = function() {
            var e, r = jQuery("#header-landing").height(),
                o = jQuery("#menubar-section").height();
            e = -r;
            for (var c = n.scrollTop(), p = i.height(), l = p - s, d = c > l ? l - c : e, h = 0; h < a.length; h++) {
                var m = a[h],
                    u = m.stickyWrapper.offset().top,
                    g = u - m.topSpacing - d;
                if (g >= c) null !== m.currentTop && (m.stickyElement.css("position", "").css("top", "").css("height", ""), m.stickyElement.parent().hasClass(m.className) && m.stickyElement.parent().animate({}, {
                    queue: !1,
                    duration: 250,
                    easing: "linear",
                    complete: function() {
                        m.stickyElement.parent().removeClass(m.className)
                    }
                }), m.currentTop = null);
                else {
                    var y = p - m.stickyElement.outerHeight() - m.topSpacing - m.bottomSpacing - c - d;
                    0 > y ? y += m.topSpacing : y = m.topSpacing, m.currentTop != y && (m.stickyElement.css("position", "fixed").css("top", y).css("height", o), "undefined" != typeof m.getWidthFrom && m.stickyElement.css("width", t(m.getWidthFrom).width()), m.stickyElement.parent().addClass(m.className), m.stickyElement.parent().hasClass(m.className) || m.stickyElement.parent().animate({}, {
                        queue: !1,
                        duration: 250,
                        easing: "linear",
                        complete: function() {
                            m.stickyElement.parent().addClass(m.className)
                        }
                    }), m.currentTop = y)
                }
            }
        },
        o = function() {
            s = n.height()
        },
        c = {
            init: function(n) {
                var i = t.extend(e, n);
                return this.each(function() {
                    var e = t(this),
                        n = e.attr("id"),
                        s = t("<div></div>").attr("id", n + "-sticky-wrapper").addClass(i.wrapperClassName);
                    e.wrapAll(s), i.center && e.parent().css({
                        width: e.outerWidth(),
                        marginLeft: "auto",
                        marginRight: "auto"
                    }), "right" == e.css("float") && e.css({
                        "float": "none"
                    }).parent().css({
                        "float": "right"
                    });
                    var r = e.parent();
                    r.css("height", e.outerHeight()), a.push({
                        topSpacing: i.topSpacing,
                        bottomSpacing: i.bottomSpacing,
                        stickyElement: e,
                        currentTop: null,
                        stickyWrapper: r,
                        className: i.className,
                        getWidthFrom: i.getWidthFrom
                    })
                })
            },
            update: r
        };
    window.addEventListener ? (window.addEventListener("scroll", r, !1), window.addEventListener("resize", o, !1)) : window.attachEvent && (window.attachEvent("onscroll", r), window.attachEvent("onresize", o)), t.fn.sticky = function(e) {
        return c[e] ? c[e].apply(this, Array.prototype.slice.call(arguments, 1)) : "object" != typeof e && e ? void t.error("Method " + e + " does not exist on jQuery.sticky") : c.init.apply(this, arguments)
    }, t(function() {
        setTimeout(r, 0)
    })
}(jQuery);
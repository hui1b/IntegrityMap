// ajax封装
function crosGet(url, data, fun, async, fun2) {
  $.ajax({
    type: "GET",
    url: url,
    timeout: 300000,
    async: async ? true : false,
    xhrFields: {
      withCredentials: true // 携带跨域cookie
    },
    data: data,
    dataType: "json",
    success: function (result) {
      if (fun) {
        fun(result)
      }
    },
    error: function (result) {
      if (fun2) {
        fun2(result)
      }
    }
  })
}

var arrayObj, markWrap, mapData, mapWrap, numList
var mapZoom = 4
$(function () {
  getSjdt()

  mapWrap = new T.Map("mapDiv", { attributionControl: false, inertia: false })
  mapWrap.centerAndZoom(new T.LngLat(106.40969, 36.43997405227057), mapZoom)
  mapWrap.setMinZoom(4)
  mapWrap.addEventListener("dblclick", function (e) {
    var curZoom = mapWrap.getZoom()
    if (curZoom < 18) {
      curZoom = curZoom + 2
    }

    makeMap("","up")
  })

  getMapIndex()

  var mapContainer = document.getElementById("mapDiv")
  mapContainer.addEventListener(
    "wheel",
    function (event) {
      event.preventDefault() // 阻止默认的滚动行为，以避免页面滚动
      var delta = event.deltaY // 获取鼠标滚轮的滚动方向和距离
      if (delta > 0) {
        // 向下滚动，例如减小缩放级别
        mapWrap.zoomOut() // 假设 map 对象有 zoomOut 方法
      } else {
        // 向上滚动，例如增加缩放级别
        mapWrap.zoomIn() // 假设 map 对象有 zoomIn 方法
      }
      setTimeout(function () {
        makeMap("","up")
      }, 300)
    },
    { passive: false }
  )
})
function getMapIndex() {
  var catalogID = $(".mapIndex .legendbox .item.on").attr("data-id")
  var level = $(".mapIndex .legendbox .item.on").attr("data-level")
  var subCatalogID = ""
  if (level == "2") {
    subCatalogID = catalogID
    catalogID = $(".mapIndex .legendbox .allItem").attr("data-id")
  }
  var searchFont = $("#searchIpt1").val().trim()
  crosGet(
    frontAppContext + "front/content/map/index",
    {
      year: $(".selectShowIndex").attr("status"),
      catalogID: catalogID,
      subCatalogID: subCatalogID,
      search: searchFont
    },
    function (response) {
      if (response.status === 1) {
        var numArr = response.data.total
        $(".numwrap .contentTotal").html(numArr.contentTotal)
        $(".numwrap .schoolTotal").html(numArr.schoolTotal)
        mapData = response.data.map.data
        numList = response.data.provinceMap.data
        makeMap("init")
        $(".changeSize").removeClass("hidden")
      }
    }
  )
}

function makeMap(backType,scaleType) {
  var searchFont = $("#searchIpt1").val().trim()
  var curZoom = mapWrap.getZoom()
  var data = mapData
  arrayObj = new Array()
  mapWrap.clearOverLays()
  if (markWrap) {
    markWrap.clearMarkers(arrayObj)
    markWrap = null
  }
  var showDetail = false
  if (curZoom > 10 && scaleType == 'up') {
    showDetail = true
  } else if(searchFont){
    showDetail = true
  }
  var curTypenum = $(".legendbox .item.on").attr("attr")
  if ((curZoom > 5 && backType != "init") || searchFont) {
    var icon = new T.Icon({
      iconUrl: siteURL + "/images/ljwhdt/locate/" + curTypenum + ".png",
      className: "iconTwo",
      iconSize: new T.Point(25, 33), //图标可视区域的大小。
      iconAnchor: new T.Point(10, 25) //图标的定位锚点。此点用来决定图标与地理位置的关系，是相对于图标左上角的偏移值，默认等于图标宽度和高度的中间值。
    })
    var styles = [
      {
        url: siteURL + "/images/ljwhdt/mapicon/" + curTypenum + ".png",
        size: [50, 50],
        offset: new T.Point(-25, -25),
        textColor: "#fff",
        textSize: 10,
        range: [0, 500]
      }
    ]
    for (var i = 0; i < data.length; i++) {
      var marker = new T.Marker(new T.LngLat(data[i].shortTitle, data[i].upTitle), { title: data[i].schoolName, icon: icon, cID: data[i].ID, info: data[i].subTitle })
      arrayObj.push(marker)
      var Summary = data[i].summary
      if (Summary) {
        Summary = Summary.substring(0, 50) + "..."
      } else {
        Summary = ""
      }
      var content = ""
      var markerInfoWin = new T.InfoWindow(content, { offset: new T.Point(0, -15) })
      addClickHandl(markerInfoWin, marker)
      if (showDetail) {
        mapWrap.addOverLay(marker)
      }
    }
    if (!showDetail) {
      setTimeout(function () {
        if (markWrap) {
          markWrap.clearMarkers(arrayObj)
          markWrap = null
        }
        markWrap = new T.MarkerClusterer(mapWrap, { markers: arrayObj, styles: styles })
      }, 500)
    }
  } else {
    $.ajax({
      type: "get",
      url: "https://api.tianditu.gov.cn/v2/administrative?keyword=156000000&childLevel=1&extensions=true&tk=660ef38b15439a82916f4d6f29a6258b",
      success: function (res) {
        if (res.status == 200) {
          var district = res.data.district[0].children
          for (var i = 0; i < district.length; i++) {
            var proCode = district[i].gb.slice(3)
            if (numList[proCode]) {
              var proNum = numList[proCode].total ? numList[proCode].total : 0
              // var iconNum = "1"
              // if (proNum < 50) {
              //   iconNum = "2"
              // }
              var marker = new T.Label({
                text: "" + proNum,
                className: "tdt-label label1",
                position: new T.LngLat(district[i].center.lng, district[i].center.lat),
                offset: new T.Point(-35, -5),
                attr: district[i].center.lng
              })
              marker.setZindex(proNum)
              mapWrap.addOverLay(marker)
              // marker.addEventListener("click", function (e) {
              //   mapWrap.centerAndZoom(new T.LngLat(e.lnglat.lng, e.lnglat.lat))
              //   setTimeout(function () {
              //     mapWrap.zoomIn()
              //   },100)
              // })
            }
          }
          $(".tdt-label.label1").css({
            "background-image": "url(" + siteURL + "images/ljwhdt/mapicon/" + curTypenum + ".png)",
            "background-size": "contain",
            "background-repeat": "no-repeat",
            "background-position": "center"
          })
        }
      }
    })
  }
}

function addClickHandl(content, marker) {
  marker.addEventListener("click", function (e) {
    var title = e.target.options.title
    var info = e.target.options.info
    $("#schoolName").html(title).attr("title", title)
    $("#schoolInfo").html(info).attr("title", info)
    getBaseinfoMap(title)
    $(".dtContent").show()
  })
}

function clearVal1() {
  $("#searchIpt1").val("")
  $(".sbox1").removeClass("hasVal")
  searchMap()
}
function searchMap() {
  clear()
  getMapIndex()
}
$("#searchIpt1").keydown(function (event) {
  if (event.keyCode == 13) {
    searchMap()
  }
})
$("#searchIpt1").on("input", function () {
  if ($(this).val()) {
    $(this).parents(".sbox1").addClass("hasVal")
  } else {
    $(this).parents(".sbox1").removeClass("hasVal")
  }
})

$(".dtContent").click(function (e) {
  e.stopPropagation()
})
// if ($(window).width() < 992) {
//   $("#mapDiv").click(function (e) {
//     e.stopPropagation()
//   })
// }
$(document).click(function (e) {
  e.stopPropagation()
  if (e.target.className.indexOf("iconTwo") > 0) {
    $(".dtContent").show()
  } else {
    if ($(".dtContent").show()) {
      $(".dtContent").hide()
    }
  }
})

//  获取基地信息
function getBaseinfoMap(searchName) {
  crosGet(
    frontAppContext + "front/content/map/rank",
    {
      pageIndex: "0",
      pageSize: "500",
      siteID: siteID,
      catalogID: $(".mapIndex .legendbox .item.on").attr("data-id"),
      year: $(".selectShowIndex").attr("status"),
      search: searchName,
      sortType: "SchoolCode"
    },
    function (response) {
      if (response.status == 1) {
        let data = response.data.data
        var html = ""
        var conTem = $("#conTem").children("template").html()
        data.forEach(function (data, index) {
          html += tmpl(conTem, data)
        })
        $("#schoolCon").html(html)
      }
    }
  )
}

function clear() {
  if (markWrap) {
    markWrap.clearMarkers(arrayObj)
    markWrap = null
  }
  mapWrap.centerAndZoom(new T.LngLat(106.40969, 36.43997405227057), mapZoom)
}

function getSjdt() {
  crosGet(
    frontAppContext + "front/content/map/rank",
    {
      pageIndex: "0",
      pageSize: "500",
      siteID: siteID,
      catalogID: $(".mapIndex .legendbox .item.on").attr("data-id"),
      year: $(".selectShowIndex").attr("status"),
      sortType: "SchoolCode"
    },
    function (response) {
      if (response.status == 1 && response.data.data && response.data.data.length) {
        var html = ""
        var trTem = $("#trTem").children("template").html()
        response.data.data.forEach(function (data, index) {
          data.num = index + 1
          data.url = siteURL + "map/detail.shtml?studioid=" + data.studioID
          html += tmpl(trTem, data)
        })
        $(".jdtable2 .tbody").html(html)


        if ($('.ljzh2026-index').length > 0) {          
          var tabSwiper = new Swiper(".tabSwiper", {
            loop: true,
            direction: "vertical",
            slidesPerView: 11,
            autoplay: 1,
            autoplayDisableOnInteraction: false,
            speed: 3000,
            freeMode: true
          })
        }else{
          var tabSwiper = new Swiper(".tabSwiper", {
            loop: true,
            direction: "vertical",
            slidesPerView: 17,
            autoplay: 1,
            autoplayDisableOnInteraction: false,
            speed: 3000,
            freeMode: true
          })
        }



      } else {
        var html = '<div class="nodata"><div class="font">暂无相关数据</div></div>'
        $(".jdtable2 .tbody").html(html)
      }
    }
  )
}

// 分类点击
$(".legendbox .item").click(function () {
  $(this).addClass("on").siblings().removeClass("on")
  clear()
  getMapIndex()
})

$(".changeSize span").click(function () {
  $(this).addClass("on").siblings("span").removeClass("on")
  var zoomNum = $(this).attr("zoom")
  var getLng = mapWrap.getCenter().getLng()
  var getLat = mapWrap.getCenter().getLat()
  mapWrap.centerAndZoom(new T.LngLat(getLng, getLat), zoomNum)
})

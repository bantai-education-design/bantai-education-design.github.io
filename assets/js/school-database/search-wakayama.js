// 和歌山県の市町村一覧（行政表示順に近い並び）
const MUNICIPALITY_ORDER = ["和歌山市", "和歌山市市", "岩出市", "御坊市", "新宮市", "有田市", "橋本市", "橋本市市", "海南市", "田辺市", "紀の川市", "紀の川市名手市", "紀の川市桃山町市", "伊都郡かつらぎ町", "伊都郡九度山町", "伊都郡高野町", "日高郡みなべ町", "日高郡印南町", "日高郡日高川町", "日高郡日高町", "日高郡由良町", "日高郡美浜町", "有田郡広川町", "有田郡有田川町", "有田郡湯浅町", "東牟婁郡串本町", "東牟婁郡北山村", "東牟婁郡古座川町", "東牟婁郡太地町", "東牟婁郡那智勝浦町", "海草郡紀美野町", "西牟婁郡すさみ町", "西牟婁郡上富田町", "西牟婁郡白浜町"];

document.addEventListener('DOMContentLoaded', () => {
    const searchApp = new SchoolSearchApp('wakayama', '和歌山県');
    searchApp.setMunicipalityOrder(MUNICIPALITY_ORDER);
    searchApp.init();
});

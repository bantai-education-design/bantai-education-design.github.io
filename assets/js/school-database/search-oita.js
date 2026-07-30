// 大分県の市町村一覧（行政表示順に近い並び）
const MUNICIPALITY_ORDER = ["中津市", "佐伯市", "別府市", "国東市", "大分市", "大分市坂ノ市", "大分市大字市", "宇佐市", "宇佐市四日市", "宇佐市大字四日市", "日田市", "日田市天瀬町五馬市", "杵築市", "津久見市", "由布市", "竹田市", "臼杵市", "臼杵市野津町大字野津市", "豊後大野市", "豊後大野市三重町市", "豊後高田市", "東国東郡姫島村", "玖珠郡九重町", "玖珠郡玖珠町", "速見郡日出町"];

document.addEventListener('DOMContentLoaded', () => {
    const searchApp = new SchoolSearchApp('oita', '大分県');
    searchApp.setMunicipalityOrder(MUNICIPALITY_ORDER);
    searchApp.init();
});

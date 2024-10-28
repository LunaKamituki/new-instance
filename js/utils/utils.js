// クエリパラメータから指定されたキーの値を返す関数
// 一致しない場合はnullを返す
function getParamValue(key){
    const url = new URL(window.location.href);
    return url.searchParams.get(key);
}

// 数値文字参照に変換する関数
function convertToNumCharRef(str){
    const splitted_str = [...str]
    var replaced_str = '';
    for(let i = 0; i < splitted_str.length; i++){
      replaced_str += "&#" + splitted_str[i].codePointAt(0) + ";";
    }
    return replaced_str
}
    
// /\s/gにmatchする文字を数値文字参照に変換する関数
function blankCharactersConvertToNumCharRef(str){
    return str.replace(/(\s)/g, matched => convertToNumericCharacterReference(matched))
}
function createChildElemFromStr({id = '', parentElemName = 'div', inner_html = '', class_str = ''}){
let parent_elem = document.createElement(parentElemName);
    if(id != ''){parent_elem.id = id};
    if(class_str != ''){parent_elem.setAttribute('class', class_str);}
    if(inner_html != ''){parent_elem.innerHTML = inner_html};
    return parent_elem
}
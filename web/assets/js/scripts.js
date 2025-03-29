/**
 * @file scripts.js
 * @description 峰云共享系统前端主脚本文件
 * @functionality
 *    - 主题切换功能(暗黑/明亮模式)
 *    - 多语言国际化支持(中英文切换)
 *    - 文件列表分页加载
 *    - 安全防护功能(禁用开发者工具等)
 * @author D.C.Y <https://dcyyd.github.io>
 * @version 1.2.0
 * @license MIT
 * @copyright © 2025 D.C.Y. All rights reserved.
 */

// 主题切换功能：切换body的dark类名并保存主题偏好到本地存储
function toggleTheme() {
    const body = document.body;
    // 切换 light 和 dark 类名
    toggleClass(body, 'light', 'dark');
    const isDark = body.classList.contains('dark');
    // 更新主题图标
    updateThemeIcon(isDark);
    // 保存主题偏好到本地存储
    savePreference('theme', isDark ? 'dark' : 'light');
}

// 辅助函数：切换元素的两个类名
function toggleClass(element, class1, class2) {
    if (element.classList.contains(class1)) {
        element.classList.remove(class1);
        element.classList.add(class2);
    } else {
        element.classList.remove(class2);
        element.classList.add(class1);
    }
}

// 更新主题图标状态
function updateThemeIcon(isDark) {
    const themeIcon = document.querySelector('.fa-moon');
    if (themeIcon) {
        // 切换月亮和太阳图标
        toggleIconClass(themeIcon, 'fa-sun', !isDark);
        // 根据主题设置图标颜色
        themeIcon.style.color = isDark ? '#fff' : '#aaa';
    }
}

// 辅助函数：切换图标的类名
function toggleIconClass(icon, targetClass, condition) {
    icon.classList.toggle(targetClass, condition);
}

// 初始化主题：从本地存储获取保存的主题或使用默认暗色主题
function initTheme() {
    const savedTheme = getPreference('theme') || 'dark';
    const isDark = savedTheme === 'dark';
    document.body.classList.toggle('dark', isDark);
    updateThemeIcon(isDark);
}

// 辅助函数：从本地存储获取偏好
function getPreference(key) {
    return localStorage.getItem(key);
}

// 辅助函数：保存偏好到本地存储
function savePreference(key, value) {
    localStorage.setItem(key, value);
}

// 初始化主题
initTheme();

// 国际化翻译字典：包含英文和中文两种语言的界面文本
const translations = {
    en: {
        title: 'Peak Cloud Share',
        uploadedFiles: '📂 File List',
        name: 'Name',
        size: 'Size',
        uploadTime: 'Upload Time',
        lastModified: 'Last Modified',
        previous: 'Previous',
        next: 'Next',
        copyright: '© 2025 <a href="https://dcyyd.github.io" target="_blank">D.C.Y</a> | v1.2.0 | built-in system'
    }, zh: {
        title: '峰云共享',
        uploadedFiles: '📂 文件列表',
        name: '名称',
        size: '大小',
        uploadTime: '上传时间',
        lastModified: '最后修改时间',
        previous: '上一页',
        next: '下一页',
        copyright: '© 2025 <a href="https://dcyyd.github.io" target="_blank">D.C.Y</a> | v1.2.0 | built-in system'
    }
};

// 切换语言功能：在英文和中文之间切换并保存偏好
function toggleLanguage() {
    const currentLang = getPreference('lang') || 'en';
    const newLang = currentLang === 'en' ? 'zh' : 'en';
    savePreference('lang', newLang);
    updateLanguage(newLang);
    // 更新语言图标颜色
    updateLanguageIconColor();
}

// 更新界面语言：根据选择的语言更新所有带data-lang-key属性的元素
function updateLanguage(lang) {
    const elements = document.querySelectorAll('[data-lang-key]');
    updateElementsWithTranslation(elements, lang);
}

// 辅助函数：根据语言更新元素的文本内容
function updateElementsWithTranslation(elements, lang) {
    elements.forEach(el => {
        const key = el.getAttribute('data-lang-key');
        if (translations[lang][key]) {
            el.innerHTML = translations[lang][key];
        }
    });
}

// 初始化语言：从本地存储获取保存的语言或使用默认英文
const savedLang = getPreference('lang') || 'en';
updateLanguage(savedLang);

// 更新语言图标颜色
function updateLanguageIconColor() {
    const isDarkTheme = document.body.classList.contains('dark');
    const languageIcon = document.querySelector('.fa-globe');
    if (languageIcon) {
        languageIcon.style.color = isDarkTheme ? '#fff' : '#aaa';
    }
}

// 分页功能：通过AJAX实现无刷新分页
function changePage(event, page) {
    event.preventDefault(); // 阻止默认链接行为
    const xhr = new XMLHttpRequest();
    xhr.open('GET', `?page=${page}`, true);
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            // 解析响应HTML并更新表格和分页控件
            const parser = new DOMParser();
            const doc = parser.parseFromString(xhr.responseText, 'text/html');
            const fileTableBody = document.getElementById('file-table-body');
            const pagination = document.getElementById('pagination');
            updateElementContent(fileTableBody, doc.getElementById('file-table-body'));
            updateElementContent(pagination, doc.getElementById('pagination'));
            // 更新语言
            updateLanguage(getPreference('lang') || 'en');
        }
    };
    xhr.send();
}

// 辅助函数：更新元素的内容
function updateElementContent(targetElement, sourceElement) {
    if (targetElement && sourceElement) {
        targetElement.innerHTML = sourceElement.innerHTML;
    }
}

// 安全防护功能：禁止右键菜单、开发者工具等
function setupSecurity() {
    // 禁止右键菜单和选择文本
    disableEvent('contextmenu');
    disableEvent('selectstart');

    // 禁用所有可能的开发者工具快捷键
    document.addEventListener('keydown', function (e) {
        const isDevToolKey = e.key === 'F12' || (e.ctrlKey && e.shiftKey && ['I', 'J', 'C', 'K', 'U'].includes(e.key)) || (e.metaKey && e.altKey && e.key === 'I') || (e.keyCode === 123);
        if (isDevToolKey) {
            preventEvent(e);
        }
    });

    // 增强型开发者工具检测
    let devtoolsOpened = false;
    const checkDevTools = function () {
        const widthThreshold = window.outerWidth - window.innerWidth > 160;
        const heightThreshold = window.outerHeight - window.innerHeight > 160;

        if ((widthThreshold || heightThreshold) && !devtoolsOpened) {
            devtoolsOpened = true;
            showDevToolsWarning();
            return;
        }

        if (!devtoolsOpened) {
            setTimeout(checkDevTools, 1000);
        }
    };

    // 双重检测机制
    let devtools = /./;
    devtools.toString = function () {
        if (!devtoolsOpened) {
            devtoolsOpened = true;
            checkDevTools();
        }
        return '';
    };
    console.log('%c', devtools);

    // 启动检测
    checkDevTools();
}

// 辅助函数：禁用特定事件
function disableEvent(eventType) {
    document.addEventListener(eventType, function (e) {
        preventEvent(e);
    });
}

// 辅助函数：阻止事件默认行为
function preventEvent(event) {
    event.preventDefault();
    event.returnValue = false;
    return false;
}

// 辅助函数：显示开发者工具打开警告
function showDevToolsWarning() {
    document.body.innerHTML = '<div style="padding:20px;text-align:center;">' + '<h2>安全警告</h2>' + '<p>检测到开发者工具已打开，请关闭后刷新页面继续使用</p>' + '<button onclick="window.location.reload()">刷新页面</button>' + '</div>';
}

setupSecurity();
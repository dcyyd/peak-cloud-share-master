/**
 * @file scripts.js
 * @description 峰云共享系统前端主脚本文件
 * @functionality
 *    - 主题切换功能(暗黑/明亮模式)
 *    - 多语言国际化支持(中英文切换)
 *    - 文件列表分页加载
 *    - 安全防护功能(禁用开发者工具等)
 *    - 文件选择与高危文件检测
 * @author D.C.Y <https://dcyyd.github.io>
 * @version 2.0.0
 * @license MIT
 * @copyright © 2025 D.C.Y. All rights reserved.
 */

// 辅助函数：阻止事件默认行为
/**
 * 阻止事件的默认行为。
 * 此函数用于简化事件默认行为的阻止操作，提高代码的可维护性。
 * @param {Event} event - 事件对象。
 */
function preventEvent(event) {
    event.preventDefault();
    event.returnValue = false;
    return false;
}

// 辅助函数：禁用特定事件
/**
 * 禁用指定类型的事件。
 * 此函数用于简化事件禁用的操作，提高代码的可维护性。
 * @param {string} eventType - 要禁用的事件类型。
 */
function disableEvent(eventType) {
    document.addEventListener(eventType, function (e) {
        preventEvent(e);
    });
}

// 辅助函数：显示开发者工具打开警告
/**
 * 当检测到开发者工具打开时，显示警告信息并要求用户关闭开发者工具。
 * 此功能确保用户在使用系统时不会进行非法操作，保护系统数据安全。
 */
function showDevToolsWarning() {
    document.body.innerHTML = `
        <div style="padding:20px;text-align:center;">
            <h2>安全警告</h2>
            <p>检测到开发者工具已打开，请关闭后刷新页面继续使用</p>
            <button onclick="window.location.reload()">刷新页面</button>
        </div>
    `;
}

// 安全防护功能：禁止右键菜单、开发者工具等
/**
 * 初始化安全防护功能，禁止用户使用右键菜单、开发者工具等，保护系统数据安全。
 * 此功能防止用户通过开发者工具进行非法操作，确保系统的安全性和稳定性。
 */
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

// 初始化安全防护，提前到文件开头执行
setupSecurity();

// 辅助函数：从本地存储获取偏好
/**
 * 从本地存储中获取指定键的偏好值。
 * 此函数用于简化本地存储的读取操作，提高代码的复用性。
 * @param {string} key - 偏好键。
 * @returns {string|null} - 偏好值，如果不存在则返回 null。
 */
function getPreference(key) {
    return localStorage.getItem(key);
}

// 辅助函数：保存偏好到本地存储
/**
 * 将指定键和值的偏好保存到本地存储。
 * 此函数用于简化本地存储的写入操作，提高代码的复用性。
 * @param {string} key - 偏好键。
 * @param {string} value - 偏好值。
 */
function savePreference(key, value) {
    localStorage.setItem(key, value);
}

// 辅助函数：切换元素的两个类名
/**
 * 切换指定元素的两个类名。
 * 此函数用于简化类名切换的操作，提高代码的可维护性。
 * @param {HTMLElement} element - 要操作的元素。
 * @param {string} class1 - 第一个类名。
 * @param {string} class2 - 第二个类名。
 */
function toggleClass(element, class1, class2) {
    if (element.classList.contains(class1)) {
        element.classList.remove(class1);
        element.classList.add(class2);
    } else {
        element.classList.remove(class2);
        element.classList.add(class1);
    }
}

// 辅助函数：切换图标的类名
/**
 * 根据条件切换图标的类名。
 * 此函数用于简化图标的类名切换操作，提高代码的可读性。
 * @param {HTMLElement} icon - 要操作的图标元素。
 * @param {string} targetClass - 目标类名。
 * @param {boolean} condition - 切换条件。
 */
function toggleIconClass(icon, targetClass, condition) {
    icon.classList.toggle(targetClass, condition);
}

// 切换主题模式（暗黑/明亮），并将用户的主题偏好保存到本地存储。
/**
 * 切换主题模式（暗黑/明亮），并将用户的主题偏好保存到本地存储。
 * 此功能增强了用户体验的个性化，同时确保用户下次访问时可以恢复之前的主题设置。
 */
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

// 更新主题图标状态
/**
 * 根据当前主题模式更新主题图标的状态和颜色。
 * 此功能提升了界面的视觉一致性和用户体验。
 * @param {boolean} isDark - 是否为暗黑模式。
 */
function updateThemeIcon(isDark) {
    const themeIcon = document.querySelector('.fa-moon');
    if (themeIcon) {
        // 切换月亮和太阳图标
        toggleIconClass(themeIcon, 'fa-sun', !isDark);
        // 根据主题设置图标颜色
        themeIcon.style.color = isDark ? '#fff' : '#aaa';
    }
}

// 初始化主题：从本地存储获取保存的主题或使用默认暗色主题
/**
 * 初始化主题模式，从本地存储中获取用户之前保存的主题偏好，如果没有则使用默认的暗色主题。
 * 此功能确保用户在每次访问时都能看到一致的主题设置。
 */
function initTheme() {
    const savedTheme = getPreference('theme') || 'dark';
    const isDark = savedTheme === 'dark';
    document.body.classList.toggle('dark', isDark);
    updateThemeIcon(isDark);
}

// 初始化主题
initTheme();

// 国际化翻译字典：包含英文和中文两种语言的界面文本
/**
 * 国际化翻译字典，包含英文和中文两种语言的界面文本。
 * 此字典用于实现系统的多语言支持，满足不同语言背景用户的需求。
 */
const translations = {
    en: {
        logAnalysis: 'Log Analysis',
        logout: 'Logout',
        uploadFile: 'Upload File',
        uploadFolder: 'Upload Folder',
        submit: 'Submit Now',
        name: 'Name',
        size: 'Size',
        uploadTime: 'Upload Time',
        lastModified: 'Last Modified',
        previous: 'Previous',
        next: 'Next',
        footer_agreement_privacy_title: 'Agreement/Privacy',
        footer_privacy_policy: 'Privacy Policy',
        footer_developer_title: 'Developer',
        footer_development_docs: 'Development Docs',
        footer_project_repo: 'Project Repo',
        footer_copyright_title: 'Copyright Information',
        footer_version: 'v2.0.0',
        footer_internal_system: 'Internal System'
    }, zh: {
        logAnalysis: '日志分析',
        logout: '登出',
        uploadFile: '上传文件',
        uploadFolder: '上传文件夹',
        submit: '立即提交',
        name: '名称',
        size: '大小',
        uploadTime: '上传时间',
        lastModified: '最后修改时间',
        previous: '上一页',
        next: '下一页',
        footer_agreement_privacy_title: '协议 / 隐私',
        footer_privacy_policy: '隐私条款',
        footer_developer_title: '开发者',
        footer_development_docs: '开发文档',
        footer_project_repo: '项目仓库',
        footer_copyright_title: '版权信息',
        footer_version: 'v2.0.0',
        footer_internal_system: '峰云内部系统'
    }
};

// 辅助函数：根据语言更新元素的文本内容
/**
 * 根据指定的语言更新元素的文本内容。
 * 此函数用于简化界面文本的翻译更新操作，提高代码的可维护性。
 * @param {NodeList} elements - 要更新的元素列表。
 * @param {string} lang - 要使用的语言（'en' 或 'zh'）。
 */
function updateElementsWithTranslation(elements, lang) {
    elements.forEach((el) => {
        const key = el.getAttribute('data-lang-key');
        if (translations[lang][key]) {
            el.innerHTML = translations[lang][key];
        }
    });
}

// 更新界面语言：根据选择的语言更新所有带 data-lang-key 属性的元素
/**
 * 根据用户选择的语言更新所有带有 data-lang-key 属性的元素的文本内容。
 * 此功能确保系统界面文本能够及时反映用户的语言偏好。
 * @param {string} lang - 要切换的语言（'en' 或 'zh'）。
 */
function updateLanguage(lang) {
    const elements = document.querySelectorAll('[data-lang-key]');
    updateElementsWithTranslation(elements, lang);
}

// 切换语言功能：在英文和中文之间切换并保存偏好
/**
 * 切换系统语言（英文和中文），并将用户的语言偏好保存到本地存储。
 * 此功能提升了系统的国际化程度，满足不同语言背景用户的需求。
 */
function toggleLanguage() {
    const currentLang = getPreference('lang') || 'en';
    const newLang = currentLang === 'en' ? 'zh' : 'en';
    savePreference('lang', newLang);
    updateLanguage(newLang);
    // 更新语言图标颜色
    updateLanguageIconColor();
}

// 初始化语言：从本地存储获取保存的语言或使用默认英文
/**
 * 初始化系统语言，从本地存储中获取用户之前保存的语言偏好，如果没有则使用默认的英文。
 * 此功能确保用户在每次访问时都能看到一致的语言设置。
 */
const savedLang = getPreference('lang') || 'en';
updateLanguage(savedLang);

// 更新语言图标颜色
/**
 * 根据当前主题模式更新语言图标的颜色。
 * 此功能提升了界面的视觉一致性和用户体验。
 */
function updateLanguageIconColor() {
    const isDarkTheme = document.body.classList.contains('dark');
    const languageIcon = document.querySelector('.fa-globe');
    if (languageIcon) {
        languageIcon.style.color = isDarkTheme ? '#fff' : '#aaa';
    }
}

// 监听页面滚动事件，根据滚动位置调整头部背景毛玻璃效果
/**
 * 监听页面滚动事件，根据滚动位置调整头部背景的毛玻璃效果。
 * 此功能提升了页面的视觉效果和用户体验。
 */
window.addEventListener('scroll', function () {
    const header = document.getElementById('header');
    if (window.scrollY > 0) {
        // 当页面向上滑动时，加深背景毛玻璃效果
        header.style.backdropFilter = 'blur(10px)';
    } else {
        // 当页面回到顶部时，恢复原始的背景毛玻璃效果
        header.style.backdropFilter = 'blur(6px)';
    }
});

// 辅助函数：更新元素的内容
/**
 * 更新目标元素的内容为源元素的内容。
 * 此函数用于简化元素内容的更新操作，提高代码的可维护性。
 * @param {HTMLElement} targetElement - 目标元素。
 * @param {HTMLElement} sourceElement - 源元素。
 */
function updateElementContent(targetElement, sourceElement) {
    if (targetElement && sourceElement) {
        targetElement.innerHTML = sourceElement.innerHTML;
    }
}

// 分页功能：通过 AJAX 实现无刷新分页
/**
 * 通过 AJAX 实现文件列表的无刷新分页功能。
 * 此功能提高了页面加载速度，优化了用户体验，特别是在处理大量文件时。
 * @param {Event} event - 事件对象。
 * @param {number} page - 要切换到的页码。
 */
function changePage(event, page) {
    event.preventDefault(); // 阻止默认链接行为
    const xhr = new XMLHttpRequest();
    xhr.open('GET', `?page=${page}`, true);
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            // 解析响应 HTML 并更新表格和分页控件
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

// 封装获取当前年份和下一年份的函数
/**
 * 获取当前年份和下一年份。
 * 此函数用于动态更新页面中的年份信息，确保信息的准确性。
 * @returns {Object} - 包含当前年份和下一年份的对象。
 */
function getCurrentAndNextYear() {
    const currentDate = new Date();
    const currentYear = currentDate.getFullYear();
    const nextYear = currentYear + 1;
    return {currentYear, nextYear};
}

// 封装更新元素文本内容的函数
/**
 * 更新指定元素的文本内容。
 * 此函数用于简化元素文本内容的更新操作，提高代码的可维护性。
 * @param {string} elementId - 元素的 ID。
 * @param {string} text - 要更新的文本内容。
 */
function updateElementText(elementId, text) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = text;
    }
}

// 获取当前年份和下一年份
const {currentYear, nextYear} = getCurrentAndNextYear();

// 更新年份元素的文本内容
updateElementText('current-year', currentYear);
updateElementText('next-current-year', nextYear);

// 切换表单显示
/**
 * 切换登录和注册表单的显示状态。
 * 此功能提供了便捷的用户交互方式，让用户可以轻松切换登录和注册操作。
 */
document.getElementById('showRegister').addEventListener('click', function (e) {
    e.preventDefault();
    document.getElementById('loginForm').classList.add('hidden');
    document.getElementById('registerForm').classList.remove('hidden');
    document.getElementById('formTitle').textContent = '峰云共享系统 - 注册';
});

/**
 * 切换注册和登录表单的显示状态。
 * 此功能提供了便捷的用户交互方式，让用户可以轻松切换注册和登录操作。
 */
document.getElementById('showLogin').addEventListener('click', function (e) {
    e.preventDefault();
    document.getElementById('registerForm').classList.add('hidden');
    document.getElementById('loginForm').classList.remove('hidden');
    document.getElementById('formTitle').textContent = '峰云共享系统 - 登录';
});

// 密码可见性切换功能
/**
 * 切换密码输入框的可见性。
 * 此功能提升了用户在输入密码时的体验，方便用户确认输入的密码。
 * @param {string} inputId - 密码输入框的 ID。
 */
function togglePasswordVisibility(inputId) {
    const passwordInput = document.getElementById(inputId);
    const icon = document.getElementById(`${inputId}ToggleIcon`);

    if (!passwordInput) {
        console.error('找不到密码输入框:', inputId);
        return;
    }

    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        icon.classList.replace('fa-eye-slash', 'fa-eye');
    } else {
        passwordInput.type = 'password';
        icon.classList.replace('fa-eye', 'fa-eye-slash');
    }
}

// 验证码倒计时功能
/**
 * 发送验证码并启动倒计时功能。
 * 此功能确保用户在发送验证码后需要等待一段时间才能再次发送，防止恶意攻击。
 */
function sendCode() {
    const email = document.querySelector("input[name='email']").value;
    if (!email) {
        alert('请输入邮箱地址');
        return;
    }
    fetch('/send_code', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: new URLSearchParams({email: email})
    }).then(res => {
        if (res.ok) return res.json();
        throw new Error('发送失败');
    }).then(data => {
        // 强制触发倒计时逻辑（即使返回error也启动）
        startCountdown();
        if (!data.success) {
            alert('发送失败: ' + (data.error || '未知错误'));
        }
    }).catch(error => {
        startCountdown();
        alert('请求失败，请检查网络连接');
    });
}

// 提取倒计时为独立函数
/**
 * 启动验证码倒计时功能。
 * 此函数用于控制验证码按钮的倒计时显示，确保用户在规定时间内不能再次发送验证码。
 */
function startCountdown() {
    let count = 60;
    const btn = document.getElementById('codeBtn');
    btn.disabled = true;
    const timer = setInterval(() => {
        btn.textContent = `${count}秒后重试`;
        if (count-- <= 0) {
            clearInterval(timer);
            btn.disabled = false;
            btn.textContent = "获取验证码";
        }
    }, 1000);
}

// 在表单提交时增加即时验证
/**
 * 在注册表单提交时进行即时验证，确保用户输入的信息符合要求。
 * 此功能提高了用户输入信息的准确性，减少了服务器端的验证负担。
 */
document.querySelector('#registerForm form').addEventListener('submit', function (e) {
    const email = document.getElementById('email').value;
    const password = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    // 邮箱格式验证
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        e.preventDefault();
        showErrorToast('请输入有效的邮箱地址');
        return;
    }

    // 密码复杂度验证
    const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d!@#$%^&*]{8,32}$/;
    if (!passwordRegex.test(password)) {
        e.preventDefault();
        showErrorToast('密码需8 - 32位，包含字母和数字');
        return;
    }

    if (password !== confirmPassword) {
        e.preventDefault();
        showErrorToast('两次输入的密码不一致');
        return;
    }
});

// 通用错误提示函数
/**
 * 显示通用的错误提示信息。
 * 此函数用于在页面上显示错误提示信息，提高用户体验和问题反馈效率。
 * @param {string} message - 要显示的错误信息。
 */
function showErrorToast(message) {
    const toastContainer = document.createElement('div');
    toastContainer.innerHTML = `
        <div class="p-3 bg-red-900/20 border border-red-700/30 rounded-lg flex items-center animate-fade-in">
            <i class="fas fa-exclamation-circle text-red-400 mr-3"></i>
            <span class="text-red-300 text-sm tracking-wide">${message}</span>
            <button onclick="this.parentElement.remove()" class="ml-auto text-red-400 hover:text-red-300">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    document.querySelector('main').prepend(toastContainer);

    setTimeout(() => {
        toastContainer.remove();
    }, 5000);
}

// 检测滚动位置，动态显示页脚
/**
 * 监听页面滚动事件，根据滚动位置动态显示或隐藏页脚。
 * 此功能提升了页面的布局效果和用户体验。
 */
window.addEventListener('scroll', function () {
    const footer = document.querySelector('.footer-container');
    const scrollPosition = window.innerHeight + window.scrollY;
    const documentHeight = document.body.scrollHeight;

    // 当滚动到页面底部时显示页脚
    if (scrollPosition >= documentHeight - 100) {
        footer.classList.add('visible');
    } else {
        footer.classList.remove('visible');
    }
});

// 由于 initToast 未使用，注释掉或删除
// // 初始化提示框
// /**
//  * 初始化提示框，显示所有提示框并在 5 秒后自动移除。
//  * 此功能用于在页面加载时显示提示信息，提高用户体验。
//  */
// function initToast() {
//     // 显示所有提示
//     document.querySelectorAll('.alert-toast').forEach((toast) => {
//         toast.classList.add('show');

//         // 5 秒后自动移除
//         setTimeout(() => {
//             toast.classList.remove('show');
//             setTimeout(() => toast.remove(), 500);
//         }, 5000);
//     });
// }

// 处理文件选择事件
/**
 * 处理文件选择事件，包括显示选择的文件数量和进行高危文件检测。
 * 此功能确保用户上传的文件符合系统的安全要求，保护系统数据安全。
 * @param {Event} e - 事件对象。
 */
function handleFileSelect(e) {
    const allFiles = [...document.getElementById('file-input').files, ...document.getElementById('folder-input').files];
    const container = document.getElementById('file-selection');
    const countSpan = document.getElementById('selected-count');

    if (allFiles.length > 0) {
        container.classList.remove('hidden');
        countSpan.textContent = allFiles.length;

        // 高危文件检测
        const highRiskExts = ['exe', 'bat', 'sh', 'dll', 'js', 'vbs', 'cmd', 'ps1', 'jar', 'apk', 'scr'];
        for (const file of allFiles) {
            const ext = file.name.split('.').pop().toLowerCase();
            if (highRiskExts.includes(ext)) {
                const isConfirmed = confirm(`警告：检测到高危文件类型 ${ext.toUpperCase()}!\n\n文件名: ${file.name}\n是否继续上传？`);
                if (!isConfirmed) {
                    // 清空所有文件选择
                    document.getElementById('file-input').value = '';
                    document.getElementById('folder-input').value = '';
                    container.classList.add('hidden');
                    return;
                }
            }
        }
    } else {
        container.classList.add('hidden');
    }
}

// 确保表单提交时调用 handleFileSelect 函数
/**
 * 确保在表单提交时调用 handleFileSelect 函数，进行文件选择和高危文件检测。
 * 此功能确保用户在提交表单时上传的文件符合系统的安全要求，保护系统数据安全。
 */
document.getElementById('upload-form').addEventListener('submit', function () {
    const fileInput = document.getElementById('file-input');
    const folderInput = document.getElementById('folder-input');
    if (fileInput.files.length > 0 || folderInput.files.length > 0) {
        handleFileSelect({target: {files: [...fileInput.files, ...folderInput.files]}});
    }
});

// Toast提示关闭功能
/**
 * 关闭指定的 Toast 提示框。
 * 此功能提供了用户关闭提示框的交互方式，提高了用户体验。
 */
function closeToast() {
    const toast = document.getElementById('errorToast');
    if (toast) {
        toast.remove();
    }
}

// 自动关闭Toast
/**
 * 自动关闭 Toast 提示框，在 5 秒后执行。
 * 此功能确保提示框在一定时间后自动关闭，提高了用户体验。
 */
setTimeout(() => {
    closeToast();
}, 5000);

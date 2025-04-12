-- ******************************************************
-- * 项目名称: 峰云文件共享平台数据库设计
-- * 版本: v2.0.0
-- * 作者: D.C.Y.
-- * 设计规范:
-- *   - 字符集: utf8mb4_unicode_ci
-- *   - 存储引擎: InnoDB
-- *   - 安全标准: PCI DSS L1
-- * 变更记录:
-- *   (2025-03-20) 初始版本
-- ******************************************************

-- ++++++++++++++++++++++++++++++++++++++++++++++++++++++
--  SECTION 1: 数据库初始化
-- ++++++++++++++++++++++++++++++++++++++++++++++++++++++
-- [功能] 创建核心数据库实例
-- [注意] 需要 SUPER 权限执行
CREATE DATABASE IF NOT EXISTS file_sharing
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- ++++++++++++++++++++++++++++++++++++++++++++++++++++++
--  SECTION 3: 用户主数据表 (PII Level 3)
-- ++++++++++++++++++++++++++++++++++++++++++++++++++++++
/**
* 表名: users
* 功能: 存储用户身份认证信息
* 安全控制:
*   - 加密字段: password, email
*   - 审计要求: 双时间戳追踪
* 字段规范:
*   [字段类型] [约束条件] [安全属性]
*/
CREATE TABLE IF NOT EXISTS users
(
    -- ========== 身份标识 ==========
    /* UUIDv4 (RFC 4122) */
    user_id    VARCHAR(36) PRIMARY KEY DEFAULT (UUID()) COMMENT '全局唯一标识符',

    -- ========== 认证凭证 ==========
    /* 符合 OWASP 认证规范 */
    username   VARCHAR(20) UNIQUE NOT NULL COMMENT '登录账号(唯一性约束)',
    password   VARCHAR(255)       NOT NULL COMMENT 'BCrypt哈希值(强度因子12)',

    -- ========== 联系信息 ==========
    /* 企业邮箱验证策略 */
    email      VARCHAR(255)       NOT NULL COMMENT '已验证邮箱地址(符合RFC 5322)',

    -- ========== 安全控制 ==========
    /* 账户锁定策略 */
    attempts   INT                     DEFAULT 0 COMMENT '失败尝试次数(5次触发锁定)',
    lock_time  DATETIME           NULL COMMENT '锁定解除时间(UTC时间戳)',

    -- ========== 系统审计 ==========
    /* 自动维护时间戳 */
    created_at TIMESTAMP               DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间(不可变更)',
    updated_at TIMESTAMP               DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间'
) ENGINE = InnoDB
  CHARSET = utf8mb4
    COMMENT = '用户主数据表(PII 3级)';

-- ++++++++++++++++++++++++++++++++++++++++++++++++++++++
--  SECTION 4: 验证码业务表 (PII Level 2)
-- ++++++++++++++++++++++++++++++++++++++++++++++++++++++
/**
* 表名: verification_codes
* 功能: 验证码生命周期管理
* 时效性:
*   - 有效时长: 10分钟
*   - 保留周期: 30天
* 索引策略:
*   - 组合索引: 邮箱+过期时间
*/
CREATE TABLE IF NOT EXISTS verification_codes
(
    -- ========== 主键标识 ==========
    id         INT AUTO_INCREMENT PRIMARY KEY COMMENT '代理主键',

    -- ========== 验证数据 ==========
    email      VARCHAR(255) NOT NULL COMMENT '目标邮箱地址(MD5哈希存储)',
    code       VARCHAR(6)   NOT NULL COMMENT '6位随机数(安全熵源)',

    -- ========== 时效控制 ==========
    expires_at DATETIME     NOT NULL COMMENT '失效时间(UTC时间戳)',

    -- ========== 系统审计 ==========
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间'
) ENGINE = InnoDB
  CHARSET = utf8mb4
    COMMENT = '验证码存储表(PII 2级)';

-- [索引说明]
-- idx_email_expiry: 优化登录验证查询性能
-- 覆盖场景: WHERE email=? AND expires_at>NOW()
CREATE INDEX idx_email_expiry ON verification_codes (email, expires_at);

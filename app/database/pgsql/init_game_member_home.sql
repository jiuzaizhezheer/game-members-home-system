-- 游戏会员之家系统 PostgreSQL 初始化脚本
-- 数据库：game_member_hub（由容器创建，脚本只负责建表/索引/种子数据）
-- 兼容：PostgreSQL 15，Docker 初始化（docker-compose.yml）

SET client_encoding = 'UTF8';
SET TIME ZONE 'UTC';

-- =========================
-- 用户实体（会员、商家、管理员）
-- =========================
CREATE TABLE IF NOT EXISTS users (
    id              uuid PRIMARY KEY,
    username        varchar(64) NOT NULL,
    email           varchar(255) NOT NULL,
    password_hash   varchar(255) NOT NULL,
    role            varchar(16) NOT NULL DEFAULT 'member',
    is_active       boolean NOT NULL DEFAULT true,
    avatar_url      varchar(512),
    points          numeric(12,2) NOT NULL DEFAULT 0.00,
    total_spent     numeric(12,2) NOT NULL DEFAULT 0.00,
    level           varchar(16) NOT NULL DEFAULT 'bronze',
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_users_role CHECK (role IN ('member','merchant','admin')),
    CONSTRAINT uq_users_username_role UNIQUE (username, role),
    CONSTRAINT uq_users_email_role UNIQUE (email, role)
);
COMMENT ON COLUMN users.points IS '会员积分';
COMMENT ON COLUMN users.total_spent IS '累计消费金额';
COMMENT ON COLUMN users.level IS '会员等级';

-- =========================
-- 商家实体
-- =========================
CREATE TABLE IF NOT EXISTS merchants (
    id              uuid PRIMARY KEY,
    user_id         uuid NOT NULL UNIQUE, -- 逻辑外键: users.id
    shop_name       varchar(128) NOT NULL UNIQUE,
    contact_phone   varchar(11),
    shop_desc       text,
    logo_url        varchar(512),
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

-- =========================
-- 地址实体
-- =========================
CREATE TABLE IF NOT EXISTS addresses (
    id              uuid PRIMARY KEY,
    user_id         uuid NOT NULL, -- 逻辑外键: users.id
    receiver_name   varchar(64) NOT NULL,
    phone           varchar(32) NOT NULL,
    province        varchar(64) NOT NULL,
    city            varchar(64) NOT NULL,
    district        varchar(64),
    detail          varchar(255) NOT NULL,
    is_default      boolean NOT NULL DEFAULT false,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_addresses_user ON addresses(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_addresses_user_default ON addresses(user_id) WHERE is_default = true;

-- =========================
-- 分类实体
-- =========================
CREATE TABLE IF NOT EXISTS categories (
    id              uuid PRIMARY KEY,
    name            varchar(64) NOT NULL UNIQUE,
    slug            varchar(64) NOT NULL UNIQUE,
    parent_id       uuid, -- 逻辑外键: categories.id
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id);

-- =========================
-- 商品实体
-- =========================
CREATE TABLE IF NOT EXISTS products (
    id              uuid PRIMARY KEY,
    merchant_id     uuid NOT NULL, -- 逻辑外键: merchants.id
    name            varchar(128) NOT NULL,
    sku             varchar(64) UNIQUE,
    description     text,
    price           numeric(12,2) NOT NULL CHECK (price >= 0),
    stock           integer NOT NULL DEFAULT 0 CHECK (stock >= 0),
    status          varchar(8) NOT NULL DEFAULT 'on',
    image_url       varchar(512),
    popularity_score integer NOT NULL DEFAULT 0,
    views_count     integer NOT NULL DEFAULT 0,
    sales_count     integer NOT NULL DEFAULT 0,
    favorites_count integer NOT NULL DEFAULT 0,
    likes_count     integer NOT NULL DEFAULT 0,
    rating          numeric(3,2) NOT NULL DEFAULT 5.00,
    review_count    integer NOT NULL DEFAULT 0,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_products_status CHECK (status IN ('on','off'))
);
CREATE INDEX IF NOT EXISTS idx_products_merchant ON products(merchant_id);
CREATE INDEX IF NOT EXISTS idx_products_popularity ON products(popularity_score DESC, sales_count DESC);
CREATE INDEX IF NOT EXISTS idx_products_views ON products(views_count DESC);
CREATE INDEX IF NOT EXISTS idx_products_favorites ON products(favorites_count DESC);
CREATE INDEX IF NOT EXISTS idx_products_likes ON products(likes_count DESC);
CREATE INDEX IF NOT EXISTS idx_products_rating ON products(rating DESC);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name); -- 搜索建议优化

-- =========================
-- 商品-分类 多对多关联表
-- =========================
CREATE TABLE IF NOT EXISTS product_categories (
    product_id      uuid NOT NULL, -- 逻辑外键: products.id
    category_id     uuid NOT NULL, -- 逻辑外键: categories.id
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (product_id, category_id)
);
CREATE INDEX IF NOT EXISTS idx_product_categories_category ON product_categories(category_id);

-- =========================
-- 收藏实体
-- =========================
CREATE TABLE IF NOT EXISTS favorites (
    user_id         uuid NOT NULL, -- 逻辑外键: users.id
    product_id      uuid NOT NULL, -- 逻辑外键: products.id
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, product_id)
);
CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);

-- =========================
-- 购物车实体
-- =========================
CREATE TABLE IF NOT EXISTS carts (
    id              uuid PRIMARY KEY,
    user_id         uuid NOT NULL, -- 逻辑外键: users.id
    name            varchar(128) NOT NULL DEFAULT '默认购物车',
    is_checked_out  boolean NOT NULL DEFAULT false,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

-- =========================
-- 购物车商品实体
-- =========================
CREATE TABLE IF NOT EXISTS cart_items (
    id              uuid PRIMARY KEY,
    cart_id         uuid NOT NULL, -- 逻辑外键: carts.id
    product_id      uuid NOT NULL, -- 逻辑外键: products.id
    quantity        integer NOT NULL CHECK (quantity > 0),
    unit_price      numeric(12,2) NOT NULL CHECK (unit_price >= 0),
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_cart_items_cart ON cart_items(cart_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_cart_items_cart_product ON cart_items(cart_id, product_id);

-- =========================
-- 订单实体
-- =========================
CREATE TABLE IF NOT EXISTS orders (
    id              uuid PRIMARY KEY,
    user_id         uuid NOT NULL, -- 逻辑外键: users.id
    address_id      uuid, -- 逻辑外键: addresses.id
    order_no        varchar(32) NOT NULL UNIQUE,
    status          varchar(16) NOT NULL DEFAULT 'pending',
    refund_status   varchar(16),                    -- 退款状态 (pending, approved, rejected)
    total_amount    numeric(12,2) NOT NULL CHECK (total_amount >= 0),
    user_coupon_id  uuid, -- 逻辑外键: user_coupons.id
    coupon_amount   numeric(12,2),                  -- 优惠券抵扣金额
    point_deduction_amount numeric(12,2),           -- 积分抵扣金额
    points_consumed numeric(12,2),                  -- 消耗积分数量
    paid_at         timestamptz,
    shipped_at      timestamptz,
    completed_at    timestamptz,
    courier_name    varchar(64),
    tracking_no     varchar(64),
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_orders_status CHECK (status IN ('pending','paid','shipped','completed','cancelled','refunding','refunded','closed')),
    CONSTRAINT chk_orders_refund_status CHECK (refund_status IS NULL OR refund_status IN ('pending','approved','rejected'))
);
COMMENT ON COLUMN orders.user_coupon_id IS '使用的优惠券记录ID';
COMMENT ON COLUMN orders.coupon_amount IS '优惠券抵扣金额';
COMMENT ON COLUMN orders.point_deduction_amount IS '积分抵扣金额';
COMMENT ON COLUMN orders.points_consumed IS '消耗积分数量';
CREATE INDEX IF NOT EXISTS idx_orders_user_created ON orders(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status); -- 运营/后台过滤优化

-- =========================
-- 订单项实体
-- =========================
CREATE TABLE IF NOT EXISTS order_items (
    id              uuid PRIMARY KEY,
    order_id        uuid NOT NULL, -- 逻辑外键: orders.id
    product_id      uuid NOT NULL, -- 逻辑外键: products.id
    quantity        integer NOT NULL CHECK (quantity > 0),
    unit_price      numeric(12,2) NOT NULL CHECK (unit_price >= 0),
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (order_id, product_id)
);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);

-- =========================
-- 支付实体
-- =========================
CREATE TABLE IF NOT EXISTS payments (
    id              uuid PRIMARY KEY,
    order_id        uuid NOT NULL UNIQUE, -- 逻辑外键: orders.id
    method          varchar(16) NOT NULL DEFAULT 'online',
    status          varchar(16) NOT NULL DEFAULT 'unpaid',
    amount          numeric(12,2) NOT NULL CHECK (amount >= 0),
    transaction_no  varchar(64),
    paid_at         timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_payments_method CHECK (method IN ('online','cod')),
    CONSTRAINT chk_payments_status CHECK (status IN ('unpaid','success','failed','refunded'))
);

-- =========================
-- 促销与活动
-- =========================
CREATE TABLE IF NOT EXISTS promotions (
    id              uuid PRIMARY KEY,
    merchant_id     uuid NOT NULL, -- 逻辑外键: merchants.id
    title           varchar(128) NOT NULL,
    discount_type   varchar(16) NOT NULL,
    discount_value  numeric(12,2) NOT NULL CHECK (discount_value >= 0),
    start_at        timestamptz NOT NULL,
    end_at          timestamptz NOT NULL,
    status          varchar(16) NOT NULL DEFAULT 'active',
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_promotions_type CHECK (discount_type IN ('percent','fixed')),
    CONSTRAINT chk_promotions_status CHECK (status IN ('active','inactive'))
);
CREATE INDEX IF NOT EXISTS idx_promotions_merchant ON promotions(merchant_id);
CREATE INDEX IF NOT EXISTS idx_promotions_period ON promotions(start_at, end_at);

-- =========================
-- 促销商品关联实体
-- =========================
CREATE TABLE IF NOT EXISTS promotion_products (
    promotion_id    uuid NOT NULL, -- 逻辑外键: promotions.id
    product_id      uuid NOT NULL, -- 逻辑外键: products.id
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (promotion_id, product_id)
);

-- =========================
-- 优惠券系统
-- =========================
CREATE TABLE IF NOT EXISTS coupons (
    id              uuid PRIMARY KEY,
    merchant_id     uuid, -- 逻辑外键: merchants.id (为空表示平台券)
    title           varchar(128) NOT NULL,
    description     varchar(256),
    discount_type   varchar(16) NOT NULL,
    discount_value  numeric(12, 2) NOT NULL,
    min_spend       numeric(12, 2) NOT NULL DEFAULT 0.00,
    total_quantity  integer NOT NULL DEFAULT 0,
    issued_count    integer NOT NULL DEFAULT 0,
    start_at        timestamptz NOT NULL,
    end_at          timestamptz NOT NULL,
    status          varchar(16) NOT NULL DEFAULT 'active',
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_coupons_discount_value CHECK (discount_value >= 0),
    CONSTRAINT chk_coupons_min_spend CHECK (min_spend >= 0),
    CONSTRAINT chk_coupons_total_quantity CHECK (total_quantity >= 0),
    CONSTRAINT chk_coupons_issued_count CHECK (issued_count >= 0)
);
COMMENT ON TABLE coupons IS '优惠券配置表';
CREATE INDEX IF NOT EXISTS idx_coupons_merchant ON coupons(merchant_id);

CREATE TABLE IF NOT EXISTS user_coupons (
    id              uuid PRIMARY KEY,
    user_id         uuid NOT NULL, -- 逻辑外键: users.id
    coupon_id       uuid NOT NULL, -- 逻辑外键: coupons.id
    order_id        uuid, -- 逻辑外键: orders.id
    status          varchar(16) NOT NULL DEFAULT 'unused',
    used_at         timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_user_coupons_status CHECK (status IN ('unused', 'used', 'expired'))
);
COMMENT ON TABLE user_coupons IS '用户领取的优惠券清单';
CREATE INDEX IF NOT EXISTS idx_user_coupons_user_status ON user_coupons(user_id, status);
CREATE INDEX IF NOT EXISTS idx_user_coupons_coupon ON user_coupons(coupon_id);


-- =========================
-- 社区分组实体
-- =========================
CREATE TABLE IF NOT EXISTS community_groups (
    id              uuid PRIMARY KEY,
    merchant_id     uuid, -- 逻辑外键: merchants.id (可选，为空表示官方圈子)
    name            varchar(128) NOT NULL UNIQUE,
    description     text,
    member_count    integer NOT NULL DEFAULT 0,
    post_count      integer NOT NULL DEFAULT 0,
    cover_image     varchar(512),
    is_active       boolean NOT NULL DEFAULT true,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_community_groups_merchant ON community_groups(merchant_id);
-- =========================
-- 社区分组成员实体
-- =========================
CREATE TABLE IF NOT EXISTS group_members (
    group_id        uuid NOT NULL, -- 逻辑外键: community_groups.id
    user_id         uuid NOT NULL, -- 逻辑外键: users.id
    joined_at       timestamptz NOT NULL DEFAULT now(),
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (group_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_group_members_user ON group_members(user_id);

-- =========================
-- 社区帖子实体
-- =========================
CREATE TABLE IF NOT EXISTS posts (
    id              uuid PRIMARY KEY,
    group_id        uuid NOT NULL, -- 逻辑外键: community_groups.id
    user_id         uuid NOT NULL, -- 逻辑外键: users.id
    title           varchar(255) NOT NULL,
    content         text NOT NULL,
    images          text[] DEFAULT '{}'::text[] NOT NULL,
    videos          text[] DEFAULT '{}'::text[] NOT NULL,
    view_count      integer NOT NULL DEFAULT 0,
    likes_count     integer NOT NULL DEFAULT 0,
    comment_count   integer NOT NULL DEFAULT 0,
    is_top          boolean NOT NULL DEFAULT false,
    is_hidden       boolean NOT NULL DEFAULT false,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_posts_group ON posts(group_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id, created_at DESC);

-- =========================
-- 管理员操作日志
-- =========================
CREATE TABLE IF NOT EXISTS admin_logs (
    id          uuid PRIMARY KEY,
    admin_id    uuid NOT NULL,                  -- 逻辑外键: users.id (role=admin)
    action      varchar(64) NOT NULL,           -- 操作类型，如 disable_user / verify_merchant
    target_type varchar(32) NOT NULL,           -- 操作目标类型，如 user / merchant / product
    target_id   varchar(64) NOT NULL,           -- 操作目标 ID（UUID 字符串）
    detail      jsonb,                          -- 操作详情（可选）
    created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_admin_logs_admin_id   ON admin_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_logs_created_at ON admin_logs(created_at DESC);

-- =========================
-- 订单退款售后实体
-- =========================
CREATE TABLE IF NOT EXISTS order_refunds (
    id              uuid PRIMARY KEY,
    order_id        uuid NOT NULL,                  -- 逻辑外键: orders.id
    user_id         uuid NOT NULL,                  -- 逻辑外键: users.id
    reason          varchar(255) NOT NULL,          -- 退款原因
    amount          numeric(12,2) NOT NULL CHECK (amount >= 0),
    status          varchar(16) NOT NULL DEFAULT 'pending',
    merchant_reply  varchar(255),                   -- 商家审批回复
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_order_refunds_status CHECK (status IN ('pending', 'approved', 'rejected'))
);
CREATE INDEX IF NOT EXISTS idx_order_refunds_order ON order_refunds(order_id);

-- =========================
-- 首页轮播图管理实体
-- =========================
CREATE TABLE IF NOT EXISTS banners (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title       varchar(128) NOT NULL,
    image_url   varchar(512) NOT NULL,
    link_url    varchar(512),
    sort_order  integer NOT NULL DEFAULT 0,
    is_active   boolean NOT NULL DEFAULT true,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE banners IS '首页轮播图管理表';

-- =========================
-- 订单物流追踪记录实体
-- =========================
CREATE TABLE IF NOT EXISTS order_logistics (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id        uuid NOT NULL,                  -- 逻辑外键: orders.id
    status_message  varchar(256) NOT NULL,          -- 状态描述
    location        varchar(128),                   -- 地理位置（城市/站点）
    log_time        timestamptz NOT NULL DEFAULT now(),
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE order_logistics IS '订单物流追踪记录表';
CREATE INDEX IF NOT EXISTS idx_order_logistics_order ON order_logistics(order_id);

-- =========================
-- 会员积分变动日志记录实体
-- =========================
CREATE TABLE IF NOT EXISTS point_logs (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL,                  -- 逻辑外键: users.id
    change_amount   numeric(12,2) NOT NULL,         -- 变动积分数量
    balance_after   numeric(12,2) NOT NULL,         -- 变动后余额
    reason          varchar(255) NOT NULL,          -- 变动原因
    related_id      varchar(64),                    -- 关联业务ID (如订单ID)
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE point_logs IS '会员积分变动日志记录表';
CREATE INDEX IF NOT EXISTS idx_point_logs_user ON point_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_point_logs_created ON point_logs(created_at DESC);

-- =========================
-- 系统消息通知实体
-- =========================
CREATE TABLE IF NOT EXISTS system_notifications (
    id              uuid PRIMARY KEY,
    user_id         uuid NOT NULL,
    type            varchar(20) NOT NULL,
    title           varchar(200) NOT NULL,
    content         text NOT NULL,
    link            varchar(500),
    is_read         boolean NOT NULL DEFAULT false,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fk_system_notifications_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
COMMENT ON TABLE system_notifications IS '系统消息通知表';
CREATE INDEX IF NOT EXISTS idx_system_notifications_user ON system_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_system_notifications_type ON system_notifications(type);
CREATE INDEX IF NOT EXISTS idx_system_notifications_read ON system_notifications(is_read);

-- =========================
-- 用户举报工单实体
-- =========================
CREATE TABLE IF NOT EXISTS user_reports (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    reporter_id     uuid NOT NULL,
    target_type     varchar(16) NOT NULL,
    target_id       varchar(64) NOT NULL,
    reason          varchar(64) NOT NULL,
    description     text,
    evidence_urls   text[] DEFAULT '{}'::text[] NOT NULL,
    status          varchar(16) NOT NULL DEFAULT 'pending',
    result          varchar(16),
    handled_by      uuid,
    handled_note    varchar(255),
    handled_at      timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fk_user_reports_reporter FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_reports_handled_by FOREIGN KEY (handled_by) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT chk_user_reports_target_type CHECK (target_type IN ('post', 'comment', 'product')),
    CONSTRAINT chk_user_reports_status CHECK (status IN ('pending', 'handled')),
    CONSTRAINT chk_user_reports_result CHECK (result IN ('success', 'fail'))
);
COMMENT ON TABLE user_reports IS '用户举报工单表';
CREATE INDEX IF NOT EXISTS idx_user_reports_status_created ON user_reports(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_reports_target ON user_reports(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_user_reports_reporter_created ON user_reports(reporter_id, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_reports_reporter_target_pending ON user_reports(reporter_id, target_type, target_id) WHERE status = 'pending';

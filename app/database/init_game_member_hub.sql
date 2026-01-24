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
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_users_role CHECK (role IN ('member','merchant','admin')),
    CONSTRAINT uq_users_username_role UNIQUE (username, role),
    CONSTRAINT uq_users_email_role UNIQUE (email, role)
);

-- =========================
-- 商家实体
-- =========================
CREATE TABLE IF NOT EXISTS merchants (
    id              uuid PRIMARY KEY,
    user_id         uuid NOT NULL UNIQUE, -- 逻辑外键: users.id
    shop_name       varchar(128) NOT NULL UNIQUE,
    contact_phone   varchar(11),
    shop_desc       text,
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
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_products_status CHECK (status IN ('on','off'))
);
CREATE INDEX IF NOT EXISTS idx_products_merchant ON products(merchant_id);
CREATE INDEX IF NOT EXISTS idx_products_popularity ON products(popularity_score DESC, sales_count DESC);
CREATE INDEX IF NOT EXISTS idx_products_views ON products(views_count DESC);
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
    user_id         uuid NOT NULL UNIQUE, -- 逻辑外键: users.id
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
    total_amount    numeric(12,2) NOT NULL CHECK (total_amount >= 0),
    created_at      timestamptz NOT NULL DEFAULT now(),
    paid_at         timestamptz,
    shipped_at      timestamptz,
    completed_at    timestamptz,
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chk_orders_status CHECK (status IN ('pending','paid','shipped','completed','cancelled'))
);
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
-- 客服与交流实体
-- =========================
CREATE TABLE IF NOT EXISTS messages (
    id                  uuid PRIMARY KEY,
    sender_user_id      uuid NOT NULL, -- 逻辑外键: users.id
    receiver_user_id    uuid NOT NULL, -- 逻辑外键: users.id
    order_id            uuid, -- 逻辑外键: orders.id
    content             text NOT NULL,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_messages_pair ON messages(sender_user_id, receiver_user_id, created_at DESC);

-- =========================
-- 社区分组实体
-- =========================
CREATE TABLE IF NOT EXISTS community_groups (
    id              uuid PRIMARY KEY,
    name            varchar(128) NOT NULL UNIQUE,
    description     text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
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
    likes_count     integer NOT NULL DEFAULT 0,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_posts_group ON posts(group_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id, created_at DESC);

-- =========================
-- 社区帖子评论实体
-- =========================
CREATE TABLE IF NOT EXISTS comments (
    id              uuid PRIMARY KEY,
    post_id         uuid NOT NULL, -- 逻辑外键: posts.id
    user_id         uuid NOT NULL, -- 逻辑外键: users.id
    content         text NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id, created_at DESC);

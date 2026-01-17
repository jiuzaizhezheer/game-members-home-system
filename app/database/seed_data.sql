-- 种子数据：用于开发和测试
-- 注意：密码为 Test123456，使用 bcrypt 加密

-- 测试分类
INSERT INTO categories (id, name, slug, parent_id, created_at, updated_at) VALUES
  ('01938000-0000-7000-0000-000000000001', '游戏', 'games', NULL, NOW(), NOW()),
  ('01938000-0000-7000-0000-000000000002', '手办', 'figures', NULL, NOW(), NOW()),
  ('01938000-0000-7000-0000-000000000003', '周边', 'merchandise', NULL, NOW(), NOW()),
  ('01938000-0000-7000-0000-000000000004', 'PC游戏', 'pc-games', '01938000-0000-7000-0000-000000000001', NOW(), NOW()),
  ('01938000-0000-7000-0000-000000000005', '主机游戏', 'console-games', '01938000-0000-7000-0000-000000000001', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 测试商家用户账号
-- password: Test123456
INSERT INTO users (id, username, email, password_hash, role, is_active, created_at, updated_at) VALUES
  ('01938001-0000-7000-0000-000000000001', 'merchant_test', 'merchant@test.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8.X4O5TLx8Y8.pVXnKe', 'merchant', true, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 测试管理员账号
-- password: Admin123456
INSERT INTO users (id, username, email, password_hash, role, is_active, created_at, updated_at) VALUES
  ('01938002-0000-7000-0000-000000000001', 'admin_test', 'admin@test.com', '$2b$12$r9h/cIPz5rTJU0.CPYKGSuE8BvH8ORJ4bQPd8.9NOBOlvM0h4S.qS', 'admin', true, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 测试商家信息
INSERT INTO merchants (id, user_id, shop_name, contact_phone, shop_desc, created_at, updated_at) VALUES
  ('01938003-0000-7000-0000-000000000001', '01938001-0000-7000-0000-000000000001', '测试游戏商店', '13800138000', '专注提供优质游戏产品和周边', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 测试商品
INSERT INTO products (id, merchant_id, name, sku, description, price, stock, status, image_url, created_at, updated_at) VALUES
  ('01938004-0000-7000-0000-000000000001', '01938003-0000-7000-0000-000000000001', '艾尔登法环', 'GAME-ER-001', '开放世界动作RPG游戏，FromSoftware制作', 298.00, 100, 'on', NULL, NOW(), NOW()),
  ('01938004-0000-7000-0000-000000000002', '01938003-0000-7000-0000-000000000001', '塞尔达传说：王国之泪', 'GAME-ZELDA-001', '任天堂开放世界冒险游戏', 398.00, 50, 'on', NULL, NOW(), NOW()),
  ('01938004-0000-7000-0000-000000000003', '01938003-0000-7000-0000-000000000001', '高达RX-78-2模型', 'FIG-GUNDAM-001', '1:144比例高达模型套件', 158.00, 30, 'on', NULL, NOW(), NOW()),
  ('01938004-0000-7000-0000-000000000004', '01938003-0000-7000-0000-000000000001', '宝可梦皮卡丘手办', 'FIG-PIKA-001', '官方授权皮卡丘收藏手办', 88.00, 200, 'on', NULL, NOW(), NOW()),
  ('01938004-0000-7000-0000-000000000005', '01938003-0000-7000-0000-000000000001', '原神周边T恤', 'MERCH-GI-001', '原神联名款T恤，纯棉材质', 128.00, 150, 'off', NULL, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 商品分类关联
INSERT INTO product_categories (product_id, category_id, created_at, updated_at) VALUES
  ('01938004-0000-7000-0000-000000000001', '01938000-0000-7000-0000-000000000001', NOW(), NOW()),
  ('01938004-0000-7000-0000-000000000001', '01938000-0000-7000-0000-000000000004', NOW(), NOW()),
  ('01938004-0000-7000-0000-000000000002', '01938000-0000-7000-0000-000000000001', NOW(), NOW()),
  ('01938004-0000-7000-0000-000000000002', '01938000-0000-7000-0000-000000000005', NOW(), NOW()),
  ('01938004-0000-7000-0000-000000000003', '01938000-0000-7000-0000-000000000002', NOW(), NOW()),
  ('01938004-0000-7000-0000-000000000004', '01938000-0000-7000-0000-000000000002', NOW(), NOW()),
  ('01938004-0000-7000-0000-000000000005', '01938000-0000-7000-0000-000000000003', NOW(), NOW())
ON CONFLICT (product_id, category_id) DO NOTHING;

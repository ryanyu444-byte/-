# coding=utf-8
"""
亚马逊商品页面图片创作工作流工具

为亚马逊卖家提供整套商品页面图片（主图、副图、A+页面）的创作工作流规划，
包含图片规格要求、创意方向建议、拍摄/设计指南和合规检查清单。
"""

import json
from datetime import datetime
from typing import Dict, List, Optional


# ==================== 亚马逊图片规格常量 ====================

MAIN_IMAGE_SPEC = {
    "name": "主图 (Main Image)",
    "dimensions": {"min": "1000x1000", "recommended": "2000x2000", "max": "10000x10000"},
    "format": ["JPEG", "PNG", "TIFF", "GIF (非动画)"],
    "background": "纯白色 (RGB 255,255,255)",
    "requirements": [
        "产品必须占据图片面积的 85% 以上",
        "纯白色背景 (RGB 255,255,255)",
        "不得包含文字、Logo、水印、边框",
        "不得出现配件、道具或与产品无关的物体",
        "产品完整展示，不裁切",
        "无人体模特（服装类可用人体模特）",
        "图片必须清晰、专业、光线充足",
        "不得包含多角度或多变体拼图",
    ],
    "common_mistakes": [
        "背景不够纯白（偏灰或偏黄）",
        "产品占比不足 85%",
        "包含品牌 Logo 或水印",
        "图片模糊或曝光不足",
        "产品有反光或投影过重",
    ],
}

SECONDARY_IMAGE_SPEC = {
    "name": "副图 (Secondary Images)",
    "count": {"standard": "最多 8 张（含主图共 9 张）", "recommended": "6-8 张副图"},
    "dimensions": {"min": "1000x1000", "recommended": "2000x2000"},
    "format": ["JPEG", "PNG"],
    "requirements": [
        "可使用场景图、生活方式图",
        "可添加文字标注、图标、信息图表",
        "可展示产品细节、尺寸对比、使用方法",
        "可使用彩色或场景化背景",
        "每张图聚焦一个核心卖点",
        "保持整套图片风格统一",
    ],
}

A_PLUS_IMAGE_SPEC = {
    "name": "A+ 内容图片 (A+ Content / EBC)",
    "modules": [
        {
            "type": "标准对比图表",
            "dimensions": "970x600",
            "description": "用于产品参数对比，突出优势",
        },
        {
            "type": "标准四图+文字",
            "dimensions": "每张 220x220",
            "description": "多图并排展示不同功能点",
        },
        {
            "type": "宽幅横幅",
            "dimensions": "970x300",
            "description": "品牌故事或场景展示",
        },
        {
            "type": "标准图片+亮色文字覆盖",
            "dimensions": "970x300",
            "description": "品牌宣言或核心卖点",
        },
        {
            "type": "标准单图+侧边详情",
            "dimensions": "300x300 (图片) + 右侧文字",
            "description": "单个特性的图文深度说明",
        },
        {
            "type": "标准技术规格表",
            "dimensions": "970x自适应",
            "description": "详细参数/规格表格",
        },
    ],
    "requirements": [
        "不得包含外部链接或引导离开亚马逊的内容",
        "不得提及竞品品牌名称",
        "不得使用 '最佳'、'#1' 等最高级声明（除非有权威认证）",
        "不得包含保修、退换货等售后承诺",
        "不得包含价格信息或促销内容",
        "图片需清晰、专业，与品牌调性一致",
        "文字需简洁有力，避免大段描述",
    ],
}

# ==================== 副图创意模板 ====================

SECONDARY_IMAGE_TEMPLATES = [
    {
        "position": 1,
        "name": "产品全貌/角度展示",
        "purpose": "补充主图，展示不同角度",
        "tips": "45度角、侧面、背面等多角度展示，突出产品造型设计",
    },
    {
        "position": 2,
        "name": "核心卖点信息图",
        "purpose": "用图标+文字标注核心功能",
        "tips": "3-5个卖点，每个卖点配一个icon和简短文字，布局清晰",
    },
    {
        "position": 3,
        "name": "使用场景/生活方式图",
        "purpose": "展示产品在真实场景中的使用效果",
        "tips": "选择目标客群的典型使用场景，唤起情感共鸣",
    },
    {
        "position": 4,
        "name": "尺寸/规格对比图",
        "purpose": "帮助买家理解产品实际大小",
        "tips": "与常见物品对比（手机、手掌等），标注具体尺寸",
    },
    {
        "position": 5,
        "name": "细节特写图",
        "purpose": "展示材质、工艺、细节品质",
        "tips": "微距拍摄关键细节，搭配简短文字说明工艺/材质",
    },
    {
        "position": 6,
        "name": "使用步骤/安装图",
        "purpose": "降低使用门槛，减少退货",
        "tips": "分步骤展示，每步配编号和说明，简洁直观",
    },
    {
        "position": 7,
        "name": "包装清单/配件图",
        "purpose": "明确买家收到的全部内容",
        "tips": "所有物品整齐排列，逐一标注名称",
    },
    {
        "position": 8,
        "name": "品牌/认证/售后图",
        "purpose": "建立信任，消除顾虑",
        "tips": "品牌Logo、认证标志、质保信息，设计简洁大气",
    },
]


class AmazonListingTools:
    """亚马逊商品页面图片创作工作流工具类"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root

    def generate_image_workflow(
        self,
        product_name: str,
        category: Optional[str] = None,
        selling_points: Optional[List[str]] = None,
        target_audience: Optional[str] = None,
        brand_style: Optional[str] = None,
        include_aplus: bool = True,
        secondary_count: int = 7,
    ) -> Dict:
        """
        生成亚马逊商品整套页面图片的创作工作流

        Args:
            product_name: 产品名称（必需）
            category: 产品类目（如 "电子产品"、"家居用品"）
            selling_points: 核心卖点列表（3-8个）
            target_audience: 目标客群描述
            brand_style: 品牌视觉风格（如 "简约现代"、"高端商务"）
            include_aplus: 是否包含A+内容规划，默认True
            secondary_count: 副图数量，默认7，范围2-8

        Returns:
            完整的创作工作流字典
        """
        if not product_name or not product_name.strip():
            return {
                "success": False,
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": "产品名称不能为空",
                },
            }

        product_name = product_name.strip()
        secondary_count = max(2, min(8, secondary_count))

        selling_points = selling_points or []
        category = category or "通用类目"
        target_audience = target_audience or "未指定"
        brand_style = brand_style or "简约专业"

        workflow = {
            "success": True,
            "summary": {
                "description": f"亚马逊商品「{product_name}」整套页面图片创作工作流",
                "product": product_name,
                "category": category,
                "total_images": 1 + secondary_count + (5 if include_aplus else 0),
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "workflow_phases": self._build_workflow_phases(
                product_name, category, selling_points,
                target_audience, brand_style,
                include_aplus, secondary_count,
            ),
            "main_image": self._build_main_image_plan(product_name, category),
            "secondary_images": self._build_secondary_image_plan(
                product_name, category, selling_points,
                target_audience, secondary_count,
            ),
        }

        if include_aplus:
            workflow["aplus_content"] = self._build_aplus_plan(
                product_name, category, selling_points,
                target_audience, brand_style,
            )

        workflow["compliance_checklist"] = self._build_compliance_checklist(include_aplus)
        workflow["design_tips"] = self._build_design_tips(brand_style, category)

        return workflow

    def get_image_specs(self, image_type: str = "all") -> Dict:
        """
        获取亚马逊各类型图片的规格要求

        Args:
            image_type: 图片类型
                - "all": 所有类型
                - "main": 主图
                - "secondary": 副图
                - "aplus": A+内容

        Returns:
            图片规格详情
        """
        valid_types = ["all", "main", "secondary", "aplus"]
        if image_type not in valid_types:
            return {
                "success": False,
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": f"无效的图片类型: {image_type}",
                    "suggestion": f"支持的类型: {', '.join(valid_types)}",
                },
            }

        result = {"success": True, "image_type": image_type}

        if image_type in ("all", "main"):
            result["main_image"] = MAIN_IMAGE_SPEC
        if image_type in ("all", "secondary"):
            result["secondary_images"] = SECONDARY_IMAGE_SPEC
            result["secondary_templates"] = SECONDARY_IMAGE_TEMPLATES
        if image_type in ("all", "aplus"):
            result["aplus_content"] = A_PLUS_IMAGE_SPEC

        return result

    def get_creative_brief(
        self,
        product_name: str,
        category: Optional[str] = None,
        selling_points: Optional[List[str]] = None,
        target_audience: Optional[str] = None,
        brand_style: Optional[str] = None,
        competitor_urls: Optional[List[str]] = None,
    ) -> Dict:
        """
        生成图片创意简报(Creative Brief)，可直接交付给设计师或AI图片工具

        Args:
            product_name: 产品名称
            category: 产品类目
            selling_points: 核心卖点列表
            target_audience: 目标客群
            brand_style: 品牌视觉风格
            competitor_urls: 竞品链接列表（用于参考分析）

        Returns:
            Markdown格式的创意简报
        """
        if not product_name or not product_name.strip():
            return {
                "success": False,
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": "产品名称不能为空",
                },
            }

        product_name = product_name.strip()
        selling_points = selling_points or []
        category = category or "通用类目"
        target_audience = target_audience or "未指定"
        brand_style = brand_style or "简约专业"

        brief = self._generate_creative_brief_markdown(
            product_name, category, selling_points,
            target_audience, brand_style, competitor_urls,
        )

        return {
            "success": True,
            "summary": {
                "description": f"商品「{product_name}」图片创意简报",
                "product": product_name,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "creative_brief": brief,
            "usage_note": "可将此简报直接交付给设计师、摄影师或 AI 图片生成工具使用",
        }

    # ==================== 内部方法 ====================

    def _build_workflow_phases(
        self,
        product_name: str,
        category: str,
        selling_points: List[str],
        target_audience: str,
        brand_style: str,
        include_aplus: bool,
        secondary_count: int,
    ) -> List[Dict]:
        """构建工作流阶段"""
        phases = [
            {
                "phase": 1,
                "name": "前期准备",
                "tasks": [
                    "确认产品卖点排序（优先级从高到低）",
                    "竞品图片调研（Top 10 竞品 Listing 截图分析）",
                    "确定品牌视觉风格和色彩方案",
                    "准备产品实物样品（多个角度检查外观）",
                    "整理产品参数/认证/配件清单",
                ],
                "deliverables": ["卖点清单", "竞品分析报告", "视觉风格指南"],
                "estimated_effort": "调研和策划",
            },
            {
                "phase": 2,
                "name": "主图拍摄与制作",
                "tasks": [
                    "搭建白色背景摄影棚",
                    "多角度拍摄原片（正面、45度、侧面等）",
                    "精修抠图：确保纯白背景 RGB(255,255,255)",
                    "调整产品占比至 85% 以上",
                    "多设备预览检查（手机、PC端缩略图效果）",
                ],
                "deliverables": ["1张合规主图 (2000x2000 JPEG)"],
                "spec": MAIN_IMAGE_SPEC,
            },
            {
                "phase": 3,
                "name": "副图创作",
                "tasks": [
                    f"规划 {secondary_count} 张副图的内容分配",
                    "场景图拍摄/3D渲染",
                    "信息图设计（卖点图标+文字标注）",
                    "尺寸对比图制作",
                    "细节特写拍摄",
                    "统一整套图片的视觉风格",
                ],
                "deliverables": [f"{secondary_count} 张副图 (2000x2000)"],
                "content_plan": self._plan_secondary_content(
                    selling_points, secondary_count
                ),
            },
        ]

        if include_aplus:
            phases.append({
                "phase": 4,
                "name": "A+ 内容设计",
                "tasks": [
                    "选择 A+ 模块组合方案",
                    "撰写 A+ 文案（品牌故事 + 产品说明）",
                    "设计 A+ 页面图片（横幅、对比图、特性图）",
                    "品牌故事模块设计",
                    "合规审查（禁用词检查、声明核实）",
                ],
                "deliverables": ["5-7个A+模块的图片和文案"],
                "recommended_modules": self._recommend_aplus_modules(category),
            })

        phases.append({
            "phase": len(phases) + 1,
            "name": "终审与上传",
            "tasks": [
                "全套图片 合规性自查（见 compliance_checklist）",
                "手机端缩略图效果验证",
                "图片文件格式和尺寸最终确认",
                "上传至 Amazon Seller Central",
                "A/B 测试计划（可选：Manage Your Experiments）",
            ],
            "deliverables": ["全套已上传的产品图片"],
        })

        return phases

    def _build_main_image_plan(self, product_name: str, category: str) -> Dict:
        """构建主图制作方案"""
        angle_suggestions = {
            "电子产品": "建议45度角展示，体现产品厚度和接口；屏幕显示产品UI界面",
            "服装": "正面平铺或人体模特穿着展示，展示整体版型",
            "家居用品": "正面微俯角拍摄，展示产品主体和纹理",
            "食品": "正面展示包装，色彩饱和度适当提高",
            "美妆个护": "45度角展示瓶身设计，质感光影处理",
            "运动户外": "动态角度展示，突出产品线条",
            "玩具": "正面展示，色彩鲜明，展示产品完整外观",
            "通用类目": "正面或45度角展示，确保产品主体清晰完整",
        }

        return {
            "spec": MAIN_IMAGE_SPEC,
            "shooting_guide": {
                "angle": angle_suggestions.get(category, angle_suggestions["通用类目"]),
                "lighting": "柔光箱 + 侧光补光，避免硬阴影；使用反光板填充暗部",
                "post_processing": [
                    "精修抠图至纯白背景 RGB(255,255,255)",
                    "去除产品表面灰尘/瑕疵",
                    "适度提亮，保持真实色彩",
                    "确保产品面积占比 ≥ 85%",
                    "输出 2000x2000px, JPEG, sRGB 色彩空间",
                ],
            },
            "mobile_optimization": {
                "note": "70%+ 买家通过手机浏览，主图在手机端仅显示约 150x150px 缩略图",
                "tips": [
                    "确保产品在缩略图下仍可辨识",
                    "避免过多留白导致产品显小",
                    "产品主体色与白色背景需有足够对比度",
                ],
            },
        }

    def _build_secondary_image_plan(
        self,
        product_name: str,
        category: str,
        selling_points: List[str],
        target_audience: str,
        count: int,
    ) -> Dict:
        """构建副图规划方案"""
        templates = SECONDARY_IMAGE_TEMPLATES[:count]

        image_plan = []
        for i, tmpl in enumerate(templates):
            plan_item = {
                "position": i + 1,
                "type": tmpl["name"],
                "purpose": tmpl["purpose"],
                "design_tips": tmpl["tips"],
            }

            if selling_points and i == 1:
                plan_item["selling_points_to_feature"] = selling_points[:5]

            if i == 2 and target_audience != "未指定":
                plan_item["scene_suggestion"] = (
                    f"为「{target_audience}」设计使用场景，展示产品融入日常生活的画面"
                )

            image_plan.append(plan_item)

        return {
            "spec": SECONDARY_IMAGE_SPEC,
            "total_count": count,
            "image_plan": image_plan,
            "style_guide": {
                "consistency": "所有副图保持统一的字体、配色、排版风格",
                "text_rules": [
                    "字号 ≥ 24pt（手机端可读）",
                    "每张图文字不超过 30 个单词",
                    "使用品牌主色作为强调色",
                    "标题加粗，说明文字用常规字重",
                ],
                "layout_tips": [
                    "留出安全边距（图片边缘 5% 内不放关键信息）",
                    "卖点图标与文字左右或上下对齐",
                    "场景图中产品为视觉焦点",
                ],
            },
        }

    def _plan_secondary_content(
        self, selling_points: List[str], count: int
    ) -> List[Dict]:
        """根据卖点规划副图内容分配"""
        plan = []

        base_types = [
            "多角度展示",
            "卖点信息图",
            "场景图",
            "尺寸对比",
            "细节特写",
            "使用步骤",
            "包装清单",
            "品牌信任",
        ]

        for i in range(min(count, len(base_types))):
            item = {"image_number": i + 1, "content_type": base_types[i]}

            if base_types[i] == "卖点信息图" and selling_points:
                item["featured_points"] = selling_points[:5]

            plan.append(item)

        return plan

    def _build_aplus_plan(
        self,
        product_name: str,
        category: str,
        selling_points: List[str],
        target_audience: str,
        brand_style: str,
    ) -> Dict:
        """构建A+内容规划"""
        recommended = self._recommend_aplus_modules(category)

        module_plan = []
        for i, mod in enumerate(recommended):
            plan_item = {
                "order": i + 1,
                "module_type": mod["type"],
                "dimensions": mod["dimensions"],
                "content_suggestion": mod["content_suggestion"],
            }
            module_plan.append(plan_item)

        return {
            "spec": A_PLUS_IMAGE_SPEC,
            "module_plan": module_plan,
            "brand_story": {
                "recommended": True,
                "structure": [
                    "品牌起源/理念（1-2句话）",
                    "核心价值主张",
                    "差异化优势",
                    "品牌愿景",
                ],
                "visual_style": f"与品牌风格「{brand_style}」保持一致",
            },
            "copywriting_tips": [
                "标题简洁有力，不超过 10 个单词",
                "正文每段不超过 3-4 行",
                "使用列表形式呈现多个卖点",
                "在文案中自然融入长尾关键词（辅助 SEO）",
                "避免使用 '最好的'、'第一名' 等绝对性声明",
            ],
        }

    def _recommend_aplus_modules(self, category: str) -> List[Dict]:
        """根据类目推荐A+模块组合"""
        base_modules = [
            {
                "type": "宽幅横幅（品牌故事）",
                "dimensions": "970x300",
                "content_suggestion": "品牌故事横幅，展示品牌理念和产品使命",
            },
            {
                "type": "标准图片+亮色文字覆盖",
                "dimensions": "970x300",
                "content_suggestion": "核心卖点宣言，一句话打动买家",
            },
            {
                "type": "标准四图+文字",
                "dimensions": "每张 220x220",
                "content_suggestion": "4个核心功能/特性分别展示",
            },
            {
                "type": "标准单图+侧边详情",
                "dimensions": "300x300 + 文字",
                "content_suggestion": "产品最大差异化优势的深度说明",
            },
            {
                "type": "标准对比图表",
                "dimensions": "970x600",
                "content_suggestion": "自家产品不同型号/款式对比，引导选购",
            },
        ]

        category_extra = {
            "电子产品": {
                "type": "标准技术规格表",
                "dimensions": "970x自适应",
                "content_suggestion": "详细技术参数表格（处理器、内存、接口等）",
            },
            "食品": {
                "type": "标准单图+侧边详情",
                "dimensions": "300x300 + 文字",
                "content_suggestion": "原料来源和营养成分说明",
            },
            "美妆个护": {
                "type": "标准单图+侧边详情",
                "dimensions": "300x300 + 文字",
                "content_suggestion": "成分解析和使用效果展示",
            },
        }

        if category in category_extra:
            base_modules.append(category_extra[category])

        return base_modules

    def _build_compliance_checklist(self, include_aplus: bool) -> Dict:
        """构建合规检查清单"""
        checklist = {
            "main_image": [
                {"item": "背景为纯白色 RGB(255,255,255)", "critical": True},
                {"item": "产品占比 ≥ 85%", "critical": True},
                {"item": "无文字、Logo、水印、边框", "critical": True},
                {"item": "无额外道具或配件（除非是产品本身的一部分）", "critical": True},
                {"item": "尺寸 ≥ 1000x1000 px", "critical": True},
                {"item": "产品图片与实物颜色一致", "critical": False},
                {"item": "图片清晰，无模糊或噪点", "critical": False},
                {"item": "手机端缩略图下产品可辨识", "critical": False},
            ],
            "secondary_images": [
                {"item": "尺寸 ≥ 1000x1000 px", "critical": True},
                {"item": "无违规文字（无虚假宣传/误导信息）", "critical": True},
                {"item": "图片与产品实际一致", "critical": True},
                {"item": "文字可读性良好（手机端 ≥ 24pt）", "critical": False},
                {"item": "整套风格统一", "critical": False},
                {"item": "每张图聚焦一个核心信息", "critical": False},
            ],
        }

        if include_aplus:
            checklist["aplus_content"] = [
                {"item": "无外部链接或引导离开亚马逊的内容", "critical": True},
                {"item": "无竞品品牌名称提及", "critical": True},
                {"item": "无未经认证的最高级声明", "critical": True},
                {"item": "无价格/促销信息", "critical": True},
                {"item": "无保修/退换货承诺", "critical": True},
                {"item": "图片清晰且与文案匹配", "critical": False},
                {"item": "所有模块在移动端显示正常", "critical": False},
                {"item": "品牌故事内容真实准确", "critical": False},
            ]

        return checklist

    def _build_design_tips(self, brand_style: str, category: str) -> Dict:
        """构建设计建议"""
        return {
            "color_palette": {
                "advice": "建立 3-5 色品牌色板：1个主色 + 1个辅色 + 1-3个中性色",
                "apply_to": "所有副图和A+页面保持统一色彩",
            },
            "typography": {
                "primary_font": "无衬线字体（如 Montserrat、Noto Sans）适合大多数类目",
                "hierarchy": "标题 > 副标题 > 正文 > 注释，层次分明",
                "language": "英文为主（面向目标站点），关键术语可中英对照",
            },
            "photography_vs_rendering": {
                "photography": "适合有实物、强调真实感的产品（食品、服装、家居）",
                "3d_rendering": "适合电子产品、机械部件等需要展示内部结构的产品",
                "hybrid": "结合实拍场景+3D渲染细节图，是当前主流做法",
            },
            "mobile_first": {
                "principle": "70%+ 流量来自移动端，所有设计优先考虑手机显示效果",
                "tips": [
                    "文字放大，确保手机端可读",
                    "避免密集信息，留出呼吸空间",
                    "关键信息放在图片中央区域",
                    "测试时用手机实际浏览效果",
                ],
            },
            "brand_style_note": f"当前品牌风格定位：「{brand_style}」，所有视觉元素需与此风格保持一致",
        }

    def _generate_creative_brief_markdown(
        self,
        product_name: str,
        category: str,
        selling_points: List[str],
        target_audience: str,
        brand_style: str,
        competitor_urls: Optional[List[str]],
    ) -> str:
        """生成Markdown格式的创意简报"""
        parts = []

        parts.append(f"# 亚马逊商品图片创意简报\n")
        parts.append(f"**产品名称**: {product_name}")
        parts.append(f"**产品类目**: {category}")
        parts.append(f"**目标客群**: {target_audience}")
        parts.append(f"**品牌风格**: {brand_style}")
        parts.append(f"**生成日期**: {datetime.now().strftime('%Y-%m-%d')}")
        parts.append("")

        parts.append("---\n")

        if selling_points:
            parts.append("## 核心卖点（按优先级排列）\n")
            for i, sp in enumerate(selling_points, 1):
                parts.append(f"{i}. **{sp}**")
            parts.append("")

        parts.append("## 一、主图要求\n")
        parts.append(f"- 尺寸：2000 x 2000 px")
        parts.append(f"- 背景：纯白色 RGB(255,255,255)")
        parts.append(f"- 产品占比：≥ 85%")
        parts.append(f"- 禁止：文字、Logo、水印、边框、额外道具")
        parts.append(f"- 格式：JPEG, sRGB 色彩空间")
        parts.append("")

        parts.append("## 二、副图规划（7张）\n")
        parts.append("| 序号 | 类型 | 内容说明 |")
        parts.append("|------|------|----------|")
        for tmpl in SECONDARY_IMAGE_TEMPLATES[:7]:
            parts.append(f"| {tmpl['position']} | {tmpl['name']} | {tmpl['purpose']} |")
        parts.append("")

        parts.append("## 三、A+ 内容模块\n")
        parts.append("| 模块 | 尺寸 | 内容建议 |")
        parts.append("|------|------|----------|")
        parts.append("| 品牌故事横幅 | 970x300 | 品牌理念 + 使命宣言 |")
        parts.append("| 核心卖点宣言 | 970x300 | 一句话打动买家 |")
        parts.append("| 四大功能特性 | 4x 220x220 | 每个功能配图+文字 |")
        parts.append("| 差异化深度说明 | 300x300+文字 | 最大优势图文展示 |")
        parts.append("| 产品对比表 | 970x600 | 自家产品线对比 |")
        parts.append("")

        parts.append("## 四、视觉风格指南\n")
        parts.append(f"- **整体风格**: {brand_style}")
        parts.append(f"- **色彩**: 建立品牌色板 (主色+辅色+中性色)")
        parts.append(f"- **字体**: 无衬线字体，标题加粗")
        parts.append(f"- **摄影**: 柔光拍摄，保持真实色彩")
        parts.append(f"- **Mobile First**: 所有文字在手机端可读")
        parts.append("")

        if competitor_urls:
            parts.append("## 五、竞品参考\n")
            for i, url in enumerate(competitor_urls[:5], 1):
                parts.append(f"{i}. {url}")
            parts.append("")

        parts.append("## 注意事项\n")
        parts.append("- 所有图片需符合亚马逊最新图片政策")
        parts.append("- A+ 内容禁止提及竞品、价格、促销、保修")
        parts.append("- 主图严格遵守白底、无文字、无水印要求")
        parts.append("- 先完成主图，确认通过审核后再制作副图和 A+")
        parts.append("")

        parts.append("---\n")
        parts.append("*本简报由 TrendRadar MCP 自动生成，请结合实际产品情况调整*")

        return "\n".join(parts)

    # ==================== AI 生图 Prompt 生成 ====================

    def generate_image_prompts(
        self,
        product_name: str,
        product_description: Optional[str] = None,
        category: Optional[str] = None,
        selling_points: Optional[List[str]] = None,
        target_audience: Optional[str] = None,
        brand_style: Optional[str] = None,
        material: Optional[str] = None,
        color: Optional[str] = None,
        include_aplus: bool = True,
        secondary_count: int = 7,
        platforms: Optional[List[str]] = None,
    ) -> Dict:
        """
        为亚马逊商品图片生成 AI 生图提示词（Midjourney / DALL-E / Stable Diffusion）

        Args:
            product_name: 产品名称（必需）
            product_description: 产品外观描述（如 "圆柱形黑色音箱，顶部有银色按键"）
            category: 产品类目
            selling_points: 核心卖点列表
            target_audience: 目标客群
            brand_style: 品牌视觉风格
            material: 产品材质（如 "不锈钢"、"硅胶"、"铝合金"）
            color: 产品主色（如 "哑光黑"、"玫瑰金"）
            include_aplus: 是否包含 A+ 横幅 prompt
            secondary_count: 副图数量，默认7，范围2-8
            platforms: 生成哪些平台的 prompt，默认全部
                       可选: ["midjourney", "dalle", "stable_diffusion"]

        Returns:
            全套 AI 生图 prompt 字典
        """
        if not product_name or not product_name.strip():
            return {
                "success": False,
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": "产品名称不能为空",
                },
            }

        product_name = product_name.strip()
        secondary_count = max(2, min(8, secondary_count))
        selling_points = selling_points or []
        category = category or "通用类目"
        brand_style = brand_style or "简约专业"
        target_audience = target_audience or ""
        material = material or ""
        color = color or ""
        product_description = product_description or ""

        all_platforms = ["midjourney", "dalle", "stable_diffusion"]
        if platforms:
            platforms = [p for p in platforms if p in all_platforms]
        if not platforms:
            platforms = all_platforms

        product_ctx = _ProductContext(
            name=product_name,
            description=product_description,
            category=category,
            selling_points=selling_points,
            target_audience=target_audience,
            brand_style=brand_style,
            material=material,
            color=color,
        )

        result = {
            "success": True,
            "summary": {
                "description": f"亚马逊商品「{product_name}」全套 AI 生图提示词",
                "product": product_name,
                "platforms": platforms,
                "total_prompts": 1 + secondary_count + (3 if include_aplus else 0),
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "main_image_prompt": self._gen_main_image_prompt(product_ctx, platforms),
            "secondary_image_prompts": self._gen_secondary_prompts(
                product_ctx, platforms, secondary_count
            ),
        }

        if include_aplus:
            result["aplus_prompts"] = self._gen_aplus_prompts(product_ctx, platforms)

        result["usage_guide"] = {
            "midjourney": {
                "how_to_use": "将 prompt 粘贴到 Midjourney Discord 的 /imagine 命令中",
                "tip": "生成后用 U1-U4 放大，再用 Vary(Subtle) 微调",
                "recommended_params": "--ar 1:1 --v 6 --s 250",
            },
            "dalle": {
                "how_to_use": "将 prompt 粘贴到 ChatGPT (DALL-E 3) 或 OpenAI API",
                "tip": "指定 size=1024x1024, quality=hd, style=natural",
                "recommended_params": "size: 1024x1024, quality: hd",
            },
            "stable_diffusion": {
                "how_to_use": "将 prompt 和 negative_prompt 分别填入 WebUI 对应输入框",
                "tip": "推荐模型：Realistic Vision / Product Design XL",
                "recommended_params": "Steps: 30, CFG: 7, Sampler: DPM++ 2M Karras",
            },
        }

        return result

    def _gen_main_image_prompt(
        self, ctx: "_ProductContext", platforms: List[str]
    ) -> Dict:
        """生成主图 prompt（纯白底产品图）"""
        product_desc = self._build_product_phrase(ctx)

        prompts = {}

        if "midjourney" in platforms:
            prompts["midjourney"] = {
                "prompt": (
                    f"commercial product photography, {product_desc}, "
                    f"centered on pure white background, studio lighting with soft diffused light, "
                    f"product fills 85 percent of frame, sharp focus on product details, "
                    f"no text, no logo, no watermark, no shadow, no props, "
                    f"professional e-commerce product shot, photorealistic, 8k quality "
                    f"--ar 1:1 --v 6 --s 250 --style raw"
                ),
                "notes": "主图要求：纯白背景、无文字、无Logo、产品占比≥85%",
            }

        if "dalle" in platforms:
            prompts["dalle"] = {
                "prompt": (
                    f"A professional e-commerce product photograph of {product_desc}. "
                    f"The product is centered on a perfectly pure white background (RGB 255,255,255). "
                    f"Studio lighting with soft, even illumination and no harsh shadows. "
                    f"The product fills approximately 85% of the frame. "
                    f"Extremely sharp focus showing fine details and textures. "
                    f"No text, no logos, no watermarks, no borders, no additional objects or props. "
                    f"Professional commercial photography quality, photorealistic."
                ),
                "params": {"size": "1024x1024", "quality": "hd", "style": "natural"},
            }

        if "stable_diffusion" in platforms:
            prompts["stable_diffusion"] = {
                "prompt": (
                    f"(masterpiece, best quality, professional product photography:1.4), "
                    f"{product_desc}, "
                    f"centered composition, pure white background, "
                    f"studio softbox lighting, product fills 85 percent of frame, "
                    f"sharp focus, high detail, commercial photography, 8k uhd, "
                    f"e-commerce product shot"
                ),
                "negative_prompt": (
                    "text, watermark, logo, label, border, shadow, reflection, "
                    "props, accessories, human, hand, fingers, blurry, "
                    "low quality, jpeg artifacts, noise, deformed, "
                    "colored background, gradient background"
                ),
                "params": {
                    "steps": 30,
                    "cfg_scale": 7,
                    "sampler": "DPM++ 2M Karras",
                    "size": "1024x1024",
                },
            }

        return {
            "type": "主图 (Main Image)",
            "amazon_requirement": "纯白背景 RGB(255,255,255)，产品占比≥85%，无文字/Logo/水印",
            "prompts": prompts,
            "post_processing_note": "AI 生成后仍需在 Photoshop 中精修：确保背景纯白、移除瑕疵、调整占比",
        }

    def _gen_secondary_prompts(
        self, ctx: "_ProductContext", platforms: List[str], count: int
    ) -> List[Dict]:
        """生成副图 prompt"""
        product_desc = self._build_product_phrase(ctx)
        scene_hint = self._get_scene_hint(ctx)

        secondary_configs = [
            {
                "name": "多角度展示图",
                "en_desc": "product shown from multiple angles including front, side, back and 45-degree view",
                "scene": f"{product_desc}, multiple angle views, arranged neatly on clean surface",
                "bg": "light grey gradient background",
            },
            {
                "name": "核心卖点信息图",
                "en_desc": "product with highlighted key features",
                "scene": f"{product_desc}, elegant floating angle, space for text overlay and feature callouts",
                "bg": "clean minimal background with subtle brand color accents",
                "note": "生成后需用设计软件添加卖点图标和文字标注",
            },
            {
                "name": "使用场景/生活方式图",
                "en_desc": f"product in real-life usage scenario{scene_hint}",
                "scene": f"person using {product_desc}{scene_hint}, natural lifestyle moment, warm and inviting atmosphere",
                "bg": "natural environment, lifestyle setting",
            },
            {
                "name": "尺寸对比图",
                "en_desc": "product next to common objects for size reference",
                "scene": f"{product_desc} placed next to a smartphone and a hand for size comparison, clean layout",
                "bg": "clean white or light surface",
                "note": "生成后需添加尺寸标注线和数字",
            },
            {
                "name": "细节特写图",
                "en_desc": "extreme close-up of product details and texture",
                "scene": f"macro close-up shot of {product_desc}, showing material texture and craftsmanship details",
                "bg": "shallow depth of field, blurred background",
            },
            {
                "name": "使用步骤展示图",
                "en_desc": "step-by-step usage demonstration",
                "scene": f"hands demonstrating how to use {product_desc}, clean step-by-step visual guide",
                "bg": "clean neutral background",
                "note": "生成后需添加步骤编号和文字说明",
            },
            {
                "name": "包装清单图",
                "en_desc": "unboxed product with all accessories laid out",
                "scene": f"{product_desc} with all included accessories neatly arranged in flat lay composition, premium unboxing experience",
                "bg": "clean white or dark premium surface",
            },
            {
                "name": "品牌信任图",
                "en_desc": "brand and quality certification showcase",
                "scene": f"{product_desc} in premium setting conveying trust and quality, elegant brand presentation",
                "bg": "sophisticated dark or gradient background, premium feel",
                "note": "生成后需添加品牌Logo和认证标志",
            },
        ]

        results = []
        for i in range(min(count, len(secondary_configs))):
            cfg = secondary_configs[i]
            prompts = {}

            if "midjourney" in platforms:
                prompts["midjourney"] = {
                    "prompt": (
                        f"Amazon product listing photo, {cfg['en_desc']}, "
                        f"{cfg['scene']}, {cfg['bg']}, "
                        f"professional commercial photography, high quality, sharp details, "
                        f"modern clean aesthetic "
                        f"--ar 1:1 --v 6 --s 200"
                    ),
                }

            if "dalle" in platforms:
                prompts["dalle"] = {
                    "prompt": (
                        f"A professional Amazon product listing photograph: {cfg['en_desc']}. "
                        f"{cfg['scene']}. {cfg['bg']}. "
                        f"Professional commercial photography with excellent lighting and composition. "
                        f"Modern, clean aesthetic suitable for e-commerce."
                    ),
                    "params": {"size": "1024x1024", "quality": "hd", "style": "natural"},
                }

            if "stable_diffusion" in platforms:
                prompts["stable_diffusion"] = {
                    "prompt": (
                        f"(masterpiece, best quality, commercial photography:1.3), "
                        f"{cfg['scene']}, {cfg['bg']}, "
                        f"professional product photography, sharp focus, "
                        f"high detail, modern aesthetic, 8k uhd"
                    ),
                    "negative_prompt": (
                        "low quality, blurry, jpeg artifacts, noise, deformed, "
                        "ugly, bad anatomy, bad hands, extra fingers, "
                        "watermark, text overlay, logo"
                    ),
                    "params": {
                        "steps": 30,
                        "cfg_scale": 7,
                        "sampler": "DPM++ 2M Karras",
                        "size": "1024x1024",
                    },
                }

            item = {
                "position": i + 1,
                "type": cfg["name"],
                "prompts": prompts,
            }

            if cfg.get("note"):
                item["post_processing_note"] = cfg["note"]

            if i == 1 and ctx.selling_points:
                item["selling_points_for_overlay"] = ctx.selling_points[:5]

            results.append(item)

        return results

    def _gen_aplus_prompts(
        self, ctx: "_ProductContext", platforms: List[str]
    ) -> List[Dict]:
        """生成 A+ 内容图片 prompt"""
        product_desc = self._build_product_phrase(ctx)
        scene_hint = self._get_scene_hint(ctx)

        aplus_configs = [
            {
                "name": "品牌故事横幅",
                "dimensions": "970x300 (约 16:5 宽幅)",
                "ar": "--ar 16:5",
                "en_desc": "wide cinematic brand story banner",
                "scene": (
                    f"cinematic wide banner, {product_desc} in elegant premium setting, "
                    f"brand storytelling atmosphere, warm golden hour lighting, "
                    f"luxurious and aspirational mood"
                ),
            },
            {
                "name": "核心卖点宣言横幅",
                "dimensions": "970x300 (约 16:5 宽幅)",
                "ar": "--ar 16:5",
                "en_desc": "hero banner with product as centerpiece",
                "scene": (
                    f"dramatic hero shot, {product_desc} as centerpiece, "
                    f"dynamic composition with space for text overlay on left or right, "
                    f"bold modern aesthetic, premium product showcase"
                ),
                "note": "生成后需在留白区域添加核心卖点文案",
            },
            {
                "name": "场景氛围大图",
                "dimensions": "970x600 (约 16:10)",
                "ar": "--ar 16:10",
                "en_desc": f"immersive lifestyle scene with product{scene_hint}",
                "scene": (
                    f"immersive lifestyle photography, {product_desc} in natural use scenario{scene_hint}, "
                    f"warm inviting atmosphere, editorial quality, magazine-style composition"
                ),
            },
        ]

        results = []
        for cfg in aplus_configs:
            prompts = {}

            if "midjourney" in platforms:
                prompts["midjourney"] = {
                    "prompt": (
                        f"Amazon A+ content, {cfg['en_desc']}, "
                        f"{cfg['scene']}, "
                        f"professional commercial photography, cinematic composition, "
                        f"high-end brand visual "
                        f"{cfg['ar']} --v 6 --s 300 --style raw"
                    ),
                }

            if "dalle" in platforms:
                ratio_hint = cfg["dimensions"]
                prompts["dalle"] = {
                    "prompt": (
                        f"A professional Amazon A+ content image ({ratio_hint}): "
                        f"{cfg['en_desc']}. {cfg['scene']}. "
                        f"Cinematic composition, professional commercial photography, "
                        f"high-end brand visual quality."
                    ),
                    "params": {"size": "1792x1024", "quality": "hd", "style": "natural"},
                }

            if "stable_diffusion" in platforms:
                prompts["stable_diffusion"] = {
                    "prompt": (
                        f"(masterpiece, best quality, cinematic:1.4), "
                        f"{cfg['scene']}, "
                        f"professional commercial photography, premium brand visual, "
                        f"sharp focus, high detail, 8k uhd"
                    ),
                    "negative_prompt": (
                        "low quality, blurry, jpeg artifacts, noise, deformed, "
                        "text, watermark, logo, ugly, bad composition"
                    ),
                    "params": {
                        "steps": 35,
                        "cfg_scale": 7.5,
                        "sampler": "DPM++ 2M Karras",
                        "size": "1536x640",
                    },
                }

            item = {
                "position": len(results) + 1,
                "type": cfg["name"],
                "dimensions": cfg["dimensions"],
                "prompts": prompts,
            }

            if cfg.get("note"):
                item["post_processing_note"] = cfg["note"]

            results.append(item)

        return results

    # ==================== Prompt 构建辅助方法 ====================

    def _build_product_phrase(self, ctx: "_ProductContext") -> str:
        """构建产品描述短语（英文，用于 prompt）"""
        parts = []

        if ctx.description:
            parts.append(ctx.description)
        else:
            parts.append(ctx.name)

        if ctx.color:
            parts.append(ctx.color)

        if ctx.material:
            parts.append(f"made of {ctx.material}")

        return ", ".join(parts) if parts else ctx.name

    def _get_scene_hint(self, ctx: "_ProductContext") -> str:
        """根据目标客群和类目生成场景提示"""
        scene_map = {
            "电子产品": ", modern desk setup, tech-savvy environment",
            "家居用品": ", cozy home interior, warm natural light",
            "服装": ", urban street style or studio setting",
            "食品": ", kitchen counter or dining table setting",
            "美妆个护": ", bathroom vanity or dressing table, soft feminine lighting",
            "运动户外": ", outdoor adventure or gym setting, energetic atmosphere",
            "玩具": ", bright playful children's room, colorful cheerful setting",
        }

        hint = scene_map.get(ctx.category, "")

        if ctx.target_audience:
            hint += f", used by {ctx.target_audience}"

        return hint


class _ProductContext:
    """产品信息上下文（内部使用）"""

    __slots__ = (
        "name", "description", "category", "selling_points",
        "target_audience", "brand_style", "material", "color",
    )

    def __init__(
        self,
        name: str,
        description: str = "",
        category: str = "",
        selling_points: Optional[List[str]] = None,
        target_audience: str = "",
        brand_style: str = "",
        material: str = "",
        color: str = "",
    ):
        self.name = name
        self.description = description
        self.category = category
        self.selling_points = selling_points or []
        self.target_audience = target_audience
        self.brand_style = brand_style
        self.material = material
        self.color = color

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

    # ==================== 实操指南生成 ====================

    def get_practical_guide(
        self,
        product_name: str,
        skill_level: str = "beginner",
        budget: str = "low",
        tool_preference: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Dict:
        """
        生成从零到成品的实操指南：用什么工具、怎么操作、怎么后期处理

        Args:
            product_name: 产品名称
            skill_level: 技能水平 beginner/intermediate/advanced
            budget: 预算水平 low(免费/低成本) / medium(适度投入) / high(专业投入)
            tool_preference: 偏好的AI工具 midjourney/dalle/stable_diffusion/canva
            category: 产品类目

        Returns:
            完整的实操指南
        """
        if not product_name or not product_name.strip():
            return {
                "success": False,
                "error": {"code": "INVALID_PARAMETER", "message": "产品名称不能为空"},
            }

        product_name = product_name.strip()
        category = category or "通用类目"

        valid_levels = ("beginner", "intermediate", "advanced")
        if skill_level not in valid_levels:
            skill_level = "beginner"

        valid_budgets = ("low", "medium", "high")
        if budget not in valid_budgets:
            budget = "low"

        recommended_stack = self._recommend_tool_stack(skill_level, budget, tool_preference)

        guide = {
            "success": True,
            "summary": {
                "description": f"亚马逊商品「{product_name}」图片+视频制作实操指南",
                "skill_level": {"beginner": "新手", "intermediate": "进阶", "advanced": "专业"}[skill_level],
                "budget": {"low": "低成本/免费", "medium": "适度投入", "high": "专业投入"}[budget],
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "recommended_tools": recommended_stack,
            "step_by_step_image_guide": self._build_image_creation_steps(
                product_name, category, skill_level, budget, recommended_stack
            ),
            "step_by_step_video_guide": self._build_video_creation_steps(
                product_name, category, skill_level, budget, recommended_stack
            ),
            "post_processing_guide": self._build_post_processing_guide(skill_level, budget),
            "quality_check_before_upload": [
                "在手机上打开图片，检查缩略图效果（模拟买家浏览体验）",
                "主图：确认背景纯白、无文字、产品清晰",
                "副图：确认文字在手机端可读（放大看是否模糊）",
                "A+：在电脑和手机上分别预览排版效果",
                "视频：确认前3秒能抓住注意力，无黑边，声音清晰",
                "所有图片尺寸 ≥ 1000x1000px，建议 2000x2000px",
                "文件大小 < 10MB（亚马逊限制）",
            ],
            "common_beginner_mistakes": [
                {"mistake": "主图背景不够白", "fix": "用 remove.bg 免费抠图，再放到纯白画布上"},
                {"mistake": "AI生的图产品细节不准确", "fix": "用AI生成场景/背景，产品部分用真实照片替换合成"},
                {"mistake": "副图文字太小手机看不清", "fix": "文字至少24pt，用对比色，先在手机上预览"},
                {"mistake": "图片风格不统一", "fix": "先做1张定稿确认风格，再批量制作其余图片"},
                {"mistake": "A+内容被亚马逊拒审", "fix": "检查禁用词：最佳/第一/保修/价格/竞品名"},
                {"mistake": "视频前几秒没吸引力", "fix": "前3秒放产品最大卖点或使用效果，别放Logo"},
            ],
        }

        return guide

    def _recommend_tool_stack(
        self, skill_level: str, budget: str, tool_preference: Optional[str]
    ) -> Dict:
        """根据技能和预算推荐工具组合"""

        stacks = {
            ("beginner", "low"): {
                "ai_image": {
                    "primary": "ChatGPT (DALL-E 3)",
                    "cost": "ChatGPT Plus $20/月 或 免费额度",
                    "why": "操作最简单，直接对话描述就能生图，无需学习额外软件",
                    "how_to_start": [
                        "打开 chat.openai.com 或 ChatGPT App",
                        "直接输入中文描述：'帮我生成一张蓝牙音箱的亚马逊主图，纯白背景，产品居中'",
                        "不满意就继续对话调整：'背景再白一些'、'产品放大一点'",
                        "点击图片下载，选择最高分辨率",
                    ],
                    "alternative": "Microsoft Copilot (免费，内置DALL-E)",
                },
                "background_removal": {
                    "tool": "remove.bg",
                    "cost": "免费（低分辨率）",
                    "url": "https://www.remove.bg/zh",
                    "how": "上传图片 → 自动抠图 → 下载PNG透明底 → 放到白色画布上",
                },
                "editing": {
                    "tool": "Canva (在线设计)",
                    "cost": "免费版够用",
                    "url": "https://www.canva.com",
                    "how": "用于给副图添加文字标注、图标、卖点说明",
                    "how_to_start": [
                        "注册 Canva → 新建 1000x1000 或 2000x2000 自定义尺寸",
                        "上传 AI 生成的产品图作为底图",
                        "使用模板或手动添加文字、图标",
                        "导出为 PNG 或 JPEG（高质量）",
                    ],
                },
                "video": {
                    "tool": "Canva / 剪映 (CapCut)",
                    "cost": "免费",
                    "how": "用产品图片+文字动画制作简单的产品展示视频",
                },
            },
            ("beginner", "medium"): {
                "ai_image": {
                    "primary": "Midjourney",
                    "cost": "$10/月 Basic Plan",
                    "why": "生图质量最高，尤其擅长产品摄影风格",
                    "how_to_start": [
                        "访问 midjourney.com 注册账号并订阅",
                        "进入 Midjourney 的 Discord 或网页版",
                        "输入 /imagine 命令 + 英文 prompt",
                        "从4张结果中选择最好的，点 U1-U4 放大",
                        "用 Vary(Subtle) 微调细节",
                    ],
                    "alternative": "ChatGPT + DALL-E 3（操作更简单）",
                },
                "background_removal": {
                    "tool": "remove.bg Pro",
                    "cost": "$9.99/月（高分辨率输出）",
                    "url": "https://www.remove.bg/zh",
                    "how": "上传→自动抠图→高清下载→精准边缘",
                },
                "editing": {
                    "tool": "Canva Pro",
                    "cost": "$12.99/月",
                    "url": "https://www.canva.com",
                    "how": "Pro版有更多模板、素材库和一键抠图功能",
                },
                "video": {
                    "tool": "剪映专业版 / Canva Pro",
                    "cost": "免费 / $12.99/月",
                    "how": "产品图片幻灯片+转场+配乐+文字动画",
                },
            },
            ("intermediate", "medium"): {
                "ai_image": {
                    "primary": "Midjourney + ChatGPT (DALL-E 3)",
                    "cost": "MJ $10/月 + ChatGPT Plus $20/月",
                    "why": "MJ做场景图/氛围图，DALL-E做精准描述的产品图",
                    "how_to_start": [
                        "主图/白底图：用 DALL-E 3 生成（纯白背景更稳定）",
                        "场景图/生活方式图：用 Midjourney（氛围感更好）",
                        "A+横幅：用 Midjourney --ar 16:5 宽幅模式",
                    ],
                },
                "background_removal": {
                    "tool": "Photoshop (AI智能抠图) 或 Photoroom",
                    "cost": "PS $22.99/月 / Photoroom 免费版",
                    "how": "PS: 选择主体→一键抠图→精修边缘 / Photoroom: 上传自动处理",
                },
                "editing": {
                    "tool": "Photoshop + Canva",
                    "cost": "PS $22.99/月 + Canva Free",
                    "how": "PS做精修和合成，Canva做快速排版和信息图",
                },
                "video": {
                    "tool": "剪映专业版 + AI视频工具",
                    "cost": "免费 + 按需付费",
                    "how": "产品实拍+AI特效+专业转场",
                },
            },
            ("advanced", "high"): {
                "ai_image": {
                    "primary": "Midjourney + Stable Diffusion (本地部署)",
                    "cost": "MJ $30/月 + SD免费（需显卡）",
                    "why": "MJ做创意初稿，SD做精准控制（ControlNet+Inpainting）",
                    "how_to_start": [
                        "安装 Stable Diffusion WebUI (AUTOMATIC1111 或 ComfyUI)",
                        "下载产品摄影专用模型：Realistic Vision / Product Design XL",
                        "使用 ControlNet 控制产品姿态和构图",
                        "使用 Inpainting 局部修改不满意的区域",
                    ],
                },
                "background_removal": {
                    "tool": "Photoshop + 手动精修",
                    "cost": "$22.99/月",
                    "how": "AI抠图 + 手动修边 + 色彩校正",
                },
                "editing": {
                    "tool": "Photoshop + Illustrator",
                    "cost": "Adobe 全家桶 $54.99/月",
                    "how": "PS做合成精修，AI做矢量图标和信息图",
                },
                "video": {
                    "tool": "Premiere Pro / After Effects + AI视频",
                    "cost": "Adobe 全家桶 + AI视频工具",
                    "how": "专业级产品视频制作",
                },
            },
        }

        key = (skill_level, budget)
        if key not in stacks:
            closest = ("beginner", "low")
            for k in stacks:
                if k[0] == skill_level or k[1] == budget:
                    closest = k
                    break
            key = closest

        stack = stacks[key]

        if tool_preference:
            preference_map = {
                "midjourney": "Midjourney",
                "dalle": "ChatGPT (DALL-E 3)",
                "stable_diffusion": "Stable Diffusion (本地部署)",
                "canva": "Canva AI 图片生成",
            }
            if tool_preference in preference_map:
                stack["ai_image"]["user_preference"] = preference_map[tool_preference]

        return stack

    def _build_image_creation_steps(
        self, product_name: str, category: str,
        skill_level: str, budget: str, tools: Dict,
    ) -> List[Dict]:
        """构建图片制作分步教程"""
        ai_tool = tools["ai_image"]["primary"]

        steps = [
            {
                "step": 1,
                "title": "准备产品素材",
                "time": "10-30分钟",
                "actions": [
                    "用手机拍摄产品照片（多角度：正面、侧面、背面、45度、俯视）",
                    "确保光线充足（自然光最佳，或台灯补光）",
                    "白色背景纸/白墙作为背景（后续AI优化）",
                    "拍摄产品细节：材质纹理、按键、接口、Logo等",
                    "如有包装盒和配件，也一起拍",
                ],
                "tips": "手机拍照就够用，不需要专业相机。关键是光线充足+画面稳定",
            },
            {
                "step": 2,
                "title": f"用 {ai_tool} 生成主图",
                "time": "15-30分钟",
                "actions": self._get_main_image_steps(ai_tool, product_name),
                "tips": "主图最重要，多生成几张对比挑选。如果AI生成的产品外观不够准确，用真实照片抠图+AI生成的白底更可靠",
            },
            {
                "step": 3,
                "title": "主图后期处理",
                "time": "10-20分钟",
                "actions": [
                    f"打开 {tools['background_removal']['tool']} 确保背景纯白",
                    "在 Canva 或 Photoshop 中打开，新建 2000x2000px 白色画布",
                    "将抠好的产品图放入画布中央，调整大小占比 ≥ 85%",
                    "检查边缘是否有毛边或残留背景色",
                    "导出为 JPEG，质量100%，RGB色彩模式",
                ],
                "alternative": "如果AI生图已经是纯白背景且效果好，可以直接调整尺寸导出",
            },
            {
                "step": 4,
                "title": f"用 {ai_tool} 生成副图底图",
                "time": "30-60分钟",
                "actions": [
                    "按照副图类型逐张生成（场景图、细节图、使用图等）",
                    "每种类型生成3-4张备选，挑选最好的",
                    "场景图：描述产品在使用环境中的画面",
                    "细节图：描述产品材质、工艺的微距特写",
                    "使用步骤图：描述操作过程的分步画面",
                ],
                "tips": "副图允许创意发挥，不需要白底。重点是每张图传达一个清晰的卖点",
            },
            {
                "step": 5,
                "title": "副图添加文字和标注",
                "time": "60-120分钟",
                "actions": [
                    f"打开 {tools['editing']['tool']}",
                    "新建 2000x2000px 画布，导入AI生成的底图",
                    "卖点信息图：添加3-5个卖点，每个配图标+简短文字",
                    "尺寸对比图：添加尺寸标注线和数字",
                    "使用步骤图：添加步骤编号 ①②③ 和说明文字",
                    "统一字体（推荐无衬线体）、统一配色（品牌色）",
                    "文字大小 ≥ 24pt，确保手机端可读",
                ],
                "tips": "Canva有大量免费模板，搜索 'Amazon product infographic' 可以找到参考",
            },
            {
                "step": 6,
                "title": "A+ 内容图片制作",
                "time": "60-120分钟",
                "actions": [
                    "品牌横幅(970x300)：用AI生成宽幅品牌氛围图",
                    "功能特性(4x 220x220)：用Canva制作图标+文字卡片",
                    "对比图表(970x600)：用Canva表格模板制作产品对比",
                    "注意：A+内容禁止提及竞品、价格、保修",
                    "所有A+模块风格保持一致",
                ],
                "tips": "Canva 搜索 'Amazon A+ content' 有专门的模板",
            },
            {
                "step": 7,
                "title": "终审和上传",
                "time": "20-30分钟",
                "actions": [
                    "所有图片在手机上预览（模拟买家浏览）",
                    "检查主图合规（白底、无文字、占比）",
                    "检查副图文字可读性",
                    "登录 Amazon Seller Central → 编辑商品 → 上传图片",
                    "A+内容：品牌 → A+内容管理器 → 创建A+页面",
                    "提交后等待亚马逊审核（通常24-48小时）",
                ],
                "tips": "如果主图被拒，最常见的原因是背景不够白或包含了不允许的元素",
            },
        ]

        return steps

    def _get_main_image_steps(self, ai_tool: str, product_name: str) -> List[str]:
        """根据AI工具生成主图操作步骤"""
        if "DALL-E" in ai_tool or "ChatGPT" in ai_tool:
            return [
                f"打开 ChatGPT，直接发送：",
                f"'帮我生成一张{product_name}的亚马逊产品主图。"
                f"要求：纯白色背景(RGB 255,255,255)，产品居中占画面85%以上，"
                f"专业商业摄影风格，柔光灯光，超高清晰度，不要任何文字和Logo'",
                "如果产品外观不对，补充描述：'产品是...(详细描述外观、颜色、形状)'",
                "不满意就继续修改：'背景再纯白一些' / '产品再大一些' / '换个角度'",
                "满意后点击图片，选择最高分辨率下载",
            ]
        elif "Midjourney" in ai_tool:
            return [
                "打开 Midjourney (网页版或Discord)",
                f"输入: /imagine commercial product photography, {product_name}, "
                "centered on pure white background, studio lighting, "
                "product fills 85% of frame, no text, no logo, photorealistic, 8k "
                "--ar 1:1 --v 6 --s 250 --style raw",
                "等待生成4张图片，选择最佳的一张",
                "点击 U1/U2/U3/U4 放大你选中的图",
                "如需微调：点击 Vary(Subtle) 小幅变化 或 Vary(Strong) 大幅变化",
                "右键保存高清大图",
            ]
        else:
            return [
                "打开 Stable Diffusion WebUI",
                f"Prompt: (masterpiece, best quality, product photography:1.4), "
                f"{product_name}, centered, pure white background, studio lighting, 8k",
                "Negative Prompt: text, watermark, logo, shadow, blurry, low quality",
                "设置: Steps=30, CFG=7, Sampler=DPM++ 2M Karras, Size=1024x1024",
                "点击 Generate，生成多张后挑选最佳",
                "用 img2img + Inpainting 修复细节问题",
            ]

    def _build_video_creation_steps(
        self, product_name: str, category: str,
        skill_level: str, budget: str, tools: Dict,
    ) -> Dict:
        """构建视频制作教程"""
        video_tool = tools.get("video", {}).get("tool", "剪映")

        return {
            "overview": {
                "amazon_video_specs": {
                    "duration": "15-60秒（推荐30秒以内）",
                    "resolution": "1920x1080 (16:9) 或 1080x1080 (1:1)",
                    "format": "MP4, MOV",
                    "max_size": "500MB",
                    "requirements": [
                        "不得包含外部网站链接或联系方式",
                        "不得包含价格/促销信息",
                        "不得提及竞品品牌",
                        "推荐前3秒展示产品核心卖点",
                        "建议添加字幕（很多买家静音浏览）",
                    ],
                },
                "video_types": [
                    {"type": "产品展示视频", "适合": "所有产品", "description": "多角度展示产品外观和细节"},
                    {"type": "使用演示视频", "适合": "功能性产品", "description": "展示产品使用方法和效果"},
                    {"type": "生活方式视频", "适合": "提升品牌感", "description": "产品融入真实生活场景"},
                    {"type": "图片轮播视频", "适合": "最简单/零基础", "description": "将产品图片做成带动画的视频"},
                ],
            },
            "method_1_easiest": {
                "name": "图片轮播视频（最简单，0基础可做）",
                "tool": "Canva 或 剪映",
                "time": "30-60分钟",
                "steps": [
                    f"打开 Canva → 新建视频项目 (1920x1080)",
                    "上传你已经做好的产品图片（主图+副图）",
                    "每张图做一页幻灯片，每页停留3-4秒",
                    "添加转场动画（推荐：淡入淡出 或 滑动）",
                    "添加产品卖点文字（大字、醒目、简短）",
                    "添加背景音乐（Canva自带免费音乐库）",
                    "导出为 MP4 (1080p)",
                ],
                "script_template": [
                    "第1页(0-3s): 主图 + 产品名称/一句话卖点",
                    "第2页(3-6s): 核心卖点1 + 配图",
                    "第3页(6-9s): 核心卖点2 + 配图",
                    "第4页(9-12s): 核心卖点3 + 配图",
                    "第5页(12-15s): 使用场景图 + Call to Action",
                ],
            },
            "method_2_ai_video": {
                "name": "AI 视频生成（效果好，操作简单）",
                "recommended_tools": [
                    {
                        "name": "可灵 AI (Kling)",
                        "url": "https://klingai.com",
                        "cost": "免费额度 / 会员",
                        "best_for": "产品展示视频，支持图生视频",
                        "how": [
                            "上传产品图片（白底主图效果最好）",
                            "输入描述：'产品缓慢旋转360度，纯白背景，商业摄影光线'",
                            "选择视频时长和画质",
                            "生成后下载 → 在剪映中添加字幕和音乐",
                        ],
                    },
                    {
                        "name": "Runway Gen-3",
                        "url": "https://runwayml.com",
                        "cost": "$12/月起",
                        "best_for": "创意场景视频，高质量运镜",
                        "how": [
                            "上传产品图片作为参考",
                            "描述想要的视频画面和镜头运动",
                            "生成4秒片段，可以拼接多段",
                        ],
                    },
                    {
                        "name": "Pika",
                        "url": "https://pika.art",
                        "cost": "免费额度 / $8/月",
                        "best_for": "图片转视频，动态效果",
                        "how": [
                            "上传产品图片",
                            "描述想要的动态效果",
                            "生成并调整",
                        ],
                    },
                    {
                        "name": "即梦 AI (Dreamina)",
                        "url": "https://jimeng.jianying.com",
                        "cost": "免费额度",
                        "best_for": "中文友好，图生视频",
                        "how": [
                            "上传产品图片",
                            "用中文描述视频效果",
                            "生成 → 下载 → 后期编辑",
                        ],
                    },
                ],
            },
            "method_3_phone_shoot": {
                "name": "手机实拍视频（最真实，买家信任度高）",
                "tool": f"手机 + {video_tool}",
                "time": "2-4小时（拍摄+剪辑）",
                "equipment": [
                    "手机（iPhone/华为/小米，近3年的旗舰机都够用）",
                    "三脚架或手机支架（淘宝20-50元）",
                    "白色背景纸/布（淘宝10-30元）",
                    "补光灯（可选，淘宝30-100元，或用自然光）",
                ],
                "shooting_tips": [
                    "开启手机4K录制（设置→相机→4K 30fps）",
                    "横屏拍摄（16:9比例）",
                    "缓慢平稳地展示产品（旋转、翻转、打开、使用）",
                    "每个镜头拍10-15秒，后期截取最好的部分",
                    "拍摄内容：开箱→外观展示→功能演示→使用场景→配件展示",
                ],
                "editing_steps": [
                    f"导入素材到 {video_tool}",
                    "剪掉多余片段，每个镜头保留3-5秒",
                    "添加转场（推荐简洁的淡入淡出）",
                    "添加字幕文字（标注卖点，英文为主）",
                    "添加背景音乐（轻快/科技感，取决于产品类型）",
                    "调整整体时长在15-45秒",
                    "导出 1080p MP4",
                ],
            },
            "recommended_approach": self._recommend_video_approach(skill_level, budget, category),
        }

    def _recommend_video_approach(
        self, skill_level: str, budget: str, category: str
    ) -> Dict:
        """推荐最适合的视频制作方案"""
        if skill_level == "beginner" and budget == "low":
            return {
                "recommendation": "方案1 图片轮播视频",
                "reason": "零基础可操作，用已有的产品图片在 Canva 中做成视频，30分钟搞定",
                "next_step": "先做图片轮播视频上架，后续有余力再升级为 AI 视频或实拍视频",
            }
        elif skill_level == "beginner":
            return {
                "recommendation": "方案2 AI视频生成（可灵AI或即梦AI）",
                "reason": "上传产品图就能自动生成视频，效果远超图片轮播，操作也很简单",
                "next_step": "先用AI生成产品旋转展示视频，再在剪映中添加字幕",
            }
        else:
            return {
                "recommendation": "方案3 手机实拍 + AI辅助",
                "reason": "真实拍摄的视频买家信任度最高，AI工具辅助提升品质",
                "next_step": "实拍产品使用演示+AI生成品牌氛围片段，在剪映中混剪",
            }

    def _build_post_processing_guide(self, skill_level: str, budget: str) -> Dict:
        """构建后期处理指南"""
        return {
            "background_to_pure_white": {
                "description": "将主图背景处理为纯白 RGB(255,255,255)",
                "free_methods": [
                    {
                        "tool": "remove.bg",
                        "url": "https://www.remove.bg/zh",
                        "steps": [
                            "上传产品图片",
                            "自动抠图完成后下载 PNG（透明背景）",
                            "在 Canva 中新建 2000x2000 白色画布",
                            "上传透明底产品图，居中放置",
                            "导出为 JPEG",
                        ],
                    },
                    {
                        "tool": "Photoroom",
                        "url": "https://www.photoroom.com",
                        "steps": [
                            "下载 Photoroom App（手机）或打开网页版",
                            "上传图片 → 自动抠图",
                            "选择白色背景",
                            "调整产品位置和大小",
                            "导出高清图",
                        ],
                    },
                ],
                "pro_method": {
                    "tool": "Photoshop",
                    "steps": [
                        "打开产品图 → 选择 → 主体（AI自动选中产品）",
                        "Ctrl+Shift+I 反选 → Delete 删除背景",
                        "新建图层填充纯白 #FFFFFF",
                        "用画笔工具修整边缘细节",
                        "图像 → 画布大小 → 调整为 2000x2000",
                        "导出为 JPEG，质量100%，sRGB",
                    ],
                },
            },
            "adding_text_and_icons": {
                "description": "为副图添加卖点文字和图标标注",
                "recommended_tool": "Canva（最适合新手）",
                "steps": [
                    "在 Canva 搜索 'Amazon product infographic' 找模板",
                    "替换模板中的图片为你的产品图",
                    "修改文字为你的产品卖点",
                    "调整颜色匹配你的品牌色",
                    "导出为 2000x2000 JPEG",
                ],
                "design_rules": [
                    "字体：使用1-2种字体（标题粗体+正文常规）",
                    "颜色：主色+辅色+白/黑，不超过3种颜色",
                    "排版：信息层次分明，留白充足",
                    "图标：使用简洁的线性图标，Canva素材库有大量免费图标",
                ],
            },
            "resize_and_export": {
                "description": "调整尺寸并导出",
                "amazon_requirements": {
                    "main_image": "2000x2000px, JPEG, RGB, ≤10MB",
                    "secondary": "2000x2000px, JPEG/PNG, RGB, ≤10MB",
                    "aplus_banner": "970x300px 或 970x600px, JPEG/PNG",
                    "video": "1920x1080 或 1080x1080, MP4, ≤500MB",
                },
                "batch_resize_tools": [
                    "Canva: 导出时选择自定义尺寸",
                    "Birme (https://www.birme.net): 免费在线批量调整图片尺寸",
                    "Squoosh (https://squoosh.app): Google出品的图片压缩工具",
                ],
            },
        }


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

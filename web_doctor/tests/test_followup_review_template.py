from django.template.loader import render_to_string
from django.test import TestCase


class FollowupReviewTemplateTests(TestCase):
    def test_followup_config_modal_has_catalog_controls_and_htmx_hooks(self):
        context = {
            "patient": type("Patient", (), {"id": 1})(),
            "review_indicator": {
                "module_title": "复查指标",
                "title": "核心关注指标",
                "catalog": [
                    {
                        "checkup_id": 1,
                        "checkup_code": "BLOOD_ROUTINE",
                        "checkup_name": "血常规",
                        "category_name": "血液",
                        "fields": [
                            {
                                "mapping_id": 11,
                                "field_id": 21,
                                "field_code": "WBC",
                                "field_name": "白细胞计数",
                                "abbr": "WBC",
                                "unit": "10^9/L",
                                "value_type": "DECIMAL",
                                "selectable": True,
                            }
                        ],
                    }
                ],
                "selected_mapping_ids": [11],
                "selected_count": 1,
                "selected_labels": ["白细胞计数"],
                "overflow_selected_count": 0,
                "charts": [],
            },
        }

        html = render_to_string(
            "web_doctor/partials/indicators/followup_review_monitoring.html",
            context,
        )

        self.assertIn('id="followup-review-config-form"', html)
        self.assertIn('id="followup-review-catalog-json"', html)
        self.assertIn('id="followup-review-selected-json"', html)
        self.assertIn('name="review_metric_mappings"', html)
        self.assertIn("配置核心关注指标", html)
        self.assertIn("搜索检查项、指标名称、编码或缩写", html)
        self.assertIn("检查项", html)
        self.assertIn("确定", html)
        self.assertIn('x-teleport="body"', html)
        self.assertIn('style="display: none; z-index: 10050;"', html)
        self.assertIn('x-show="configOpen"', html)
        self.assertIn('hx-on:htmx:before-request="configOpen = false"', html)
        self.assertIn('hx-on:htmx:after-request="configOpen = false"', html)
        self.assertNotIn('onclick="this.closest(\'form\').style.display=\'none\'"', html)

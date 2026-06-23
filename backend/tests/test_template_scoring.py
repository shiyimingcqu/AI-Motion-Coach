import unittest
from app.services.analysis.angle_feature_service import extract_squat_features
from app.services.analysis.models import NormalizedKeypoint
from app.services.analysis.template_service import TemplateService
from app.services.analysis.feedback_service import FeedbackService


class TestAngleFeatureService(unittest.TestCase):
    """测试角度特征提取服务"""

    def test_extract_squat_features_success(self):
        """测试成功提取深蹲特征"""
        keypoints = {
            "left_shoulder": NormalizedKeypoint(x=0.4, y=0.3, visibility=0.99),
            "right_shoulder": NormalizedKeypoint(x=0.6, y=0.3, visibility=0.99),
            "left_hip": NormalizedKeypoint(x=0.4, y=0.5, visibility=0.99),
            "right_hip": NormalizedKeypoint(x=0.6, y=0.5, visibility=0.99),
            "left_knee": NormalizedKeypoint(x=0.42, y=0.7, visibility=0.99),
            "right_knee": NormalizedKeypoint(x=0.58, y=0.7, visibility=0.99),
            "left_ankle": NormalizedKeypoint(x=0.43, y=0.9, visibility=0.99),
            "right_ankle": NormalizedKeypoint(x=0.57, y=0.9, visibility=0.99),
        }

        metrics = extract_squat_features(keypoints)

        self.assertIn("knee_angle", metrics)
        self.assertIn("hip_angle", metrics)
        self.assertIn("trunk_angle", metrics)
        self.assertIn("knee_symmetry_diff", metrics)

        # 验证角度在合理范围内
        self.assertGreater(metrics["knee_angle"], 0)
        self.assertLess(metrics["knee_angle"], 180)
        self.assertGreater(metrics["hip_angle"], 0)
        self.assertLess(metrics["hip_angle"], 180)
        # trunk_angle 可能为0，所以不检查
        self.assertGreaterEqual(metrics["trunk_angle"], 0)
        self.assertLess(metrics["trunk_angle"], 180)
        self.assertGreaterEqual(metrics["knee_symmetry_diff"], 0)

    def test_extract_squat_features_missing_keypoints(self):
        """测试缺少关键点时抛出异常"""
        keypoints = {
            "left_shoulder": NormalizedKeypoint(x=0.4, y=0.3, visibility=0.99),
            "right_shoulder": NormalizedKeypoint(x=0.6, y=0.3, visibility=0.99),
        }

        with self.assertRaises(ValueError) as context:
            extract_squat_features(keypoints)

        self.assertIn("缺少关键点", str(context.exception))


class TestTemplateService(unittest.TestCase):
    """测试模板评分服务"""

    def setUp(self):
        self.template_service = TemplateService()

    def test_resample_sequence_empty(self):
        """测试空序列重采样"""
        result = self.template_service.resample_sequence([], 50)
        self.assertEqual(result, [])

    def test_resample_sequence_single_point(self):
        """测试单点序列重采样"""
        result = self.template_service.resample_sequence([100], 50)
        self.assertEqual(len(result), 50)
        self.assertTrue(all(x == 100 for x in result))

    def test_resample_sequence_multiple_points(self):
        """测试多点序列重采样"""
        original = [100, 110, 120, 130, 140]
        result = self.template_service.resample_sequence(original, 10)

        self.assertEqual(len(result), 10)
        self.assertEqual(result[0], 100)
        self.assertEqual(result[-1], 140)

    def test_score_by_template_perfect_match(self):
        """测试与模板完全匹配时得分高"""
        # 使用模板数据
        template = self.template_service.load_template("squat")
        template_frames = [
            {
                "knee_angle": angle,
                "hip_angle": template["template_sequence"]["hip_angle"][i],
                "trunk_angle": template["template_sequence"]["trunk_angle"][i],
                "knee_symmetry_diff": template["template_sequence"]["knee_symmetry_diff"][i],
            }
            for i, angle in enumerate(template["template_sequence"]["knee_angle"])
        ]

        result = self.template_service.score_by_template("squat", template_frames)

        self.assertGreater(result["score"], 90)
        self.assertEqual(result["level"], "excellent")

    def test_score_by_template_poor_match(self):
        """测试与模板差异大时得分低"""
        poor_frames = [
            {
                "knee_angle": 150,  # 与模板差异大
                "hip_angle": 160,
                "trunk_angle": 45,
                "knee_symmetry_diff": 20,
            }
        ] * 10

        result = self.template_service.score_by_template("squat", poor_frames)

        self.assertLess(result["score"], 60)
        self.assertIn("knee_angle", result["detail_scores"])
        self.assertLess(result["detail_scores"]["knee_angle"], 75)

    def test_score_by_template_empty_frames(self):
        """测试空帧数据"""
        result = self.template_service.score_by_template("squat", [])

        self.assertEqual(result["score"], 0.0)
        self.assertEqual(result["level"], "invalid")

    def test_load_template_by_template_id(self):
        """Load a storage template by its explicit template id."""
        template = self.template_service.load_template_by_id("squat_template_side_v1")

        self.assertEqual(template["action"], "squat")
        self.assertEqual(template["view"], "side")
        self.assertEqual(template["version"], "v1")
        self.assertIn("knee_angle", template["template_sequence"])

    def test_score_by_template_accepts_template_id(self):
        """Score a frame sequence against a selected reference template."""
        frames = [
            {
                "knee_angle": 170,
                "hip_angle": 150,
                "trunk_angle": 2,
                "knee_symmetry_diff": 5,
            }
        ] * 10

        result = self.template_service.score_by_template("squat", frames, template_id="squat_template_side_v1")

        self.assertIn("score", result)
        self.assertIn("knee_angle", result["detail_scores"])
        self.assertIn("knee_angle", result["differences"])


class TestFeedbackService(unittest.TestCase):
    """测试反馈生成服务"""

    def setUp(self):
        self.feedback_service = FeedbackService()

    def test_generate_feedback_good_score(self):
        """测试高分时生成正面反馈"""
        score_result = {
            "score": 92.5,
            "detail_scores": {
                "knee_angle": 90.0,
                "hip_angle": 88.0,
                "trunk_angle": 95.0,
                "knee_symmetry_diff": 92.0,
            },
            "differences": {
                "knee_angle": 3.0,
                "hip_angle": 4.0,
                "trunk_angle": 2.0,
                "knee_symmetry_diff": 2.5,
            },
        }

        feedback = self.feedback_service.generate_template_feedback(score_result)

        self.assertEqual(len(feedback["errors"]), 0)
        self.assertGreater(len(feedback["suggestions"]), 0)

    def test_generate_feedback_poor_knee_angle(self):
        """测试膝关节角度差时生成相应建议"""
        score_result = {
            "score": 65.0,
            "detail_scores": {
                "knee_angle": 70.0,  # 低于75
                "hip_angle": 80.0,
                "trunk_angle": 85.0,
                "knee_symmetry_diff": 75.0,
            },
            "differences": {
                "knee_angle": 10.0,
                "hip_angle": 5.0,
                "trunk_angle": 4.0,
                "knee_symmetry_diff": 3.0,
            },
        }

        feedback = self.feedback_service.generate_template_feedback(score_result)

        self.assertGreater(len(feedback["errors"]), 0)
        self.assertGreater(len(feedback["suggestions"]), 0)

        # 检查是否包含膝关节相关的错误或建议
        error_text = " ".join(feedback["errors"])
        suggestion_text = " ".join(feedback["suggestions"])
        has_knee_feedback = "膝" in error_text or "膝" in suggestion_text
        self.assertTrue(has_knee_feedback)

    def test_generate_feedback_poor_symmetry(self):
        """测试左右对称性差时生成相应建议"""
        score_result = {
            "score": 70.0,
            "detail_scores": {
                "knee_angle": 80.0,
                "hip_angle": 82.0,
                "trunk_angle": 85.0,
                "knee_symmetry_diff": 60.0,  # 低于75
            },
            "differences": {
                "knee_angle": 6.0,
                "hip_angle": 5.0,
                "trunk_angle": 4.0,
                "knee_symmetry_diff": 8.0,
            },
        }

        feedback = self.feedback_service.generate_template_feedback(score_result)

        self.assertGreater(len(feedback["errors"]), 0)
        self.assertGreater(len(feedback["suggestions"]), 0)

        # 检查是否包含对称性相关的错误或建议
        error_text = " ".join(feedback["errors"])
        suggestion_text = " ".join(feedback["suggestions"])
        has_symmetry_feedback = "对称" in error_text or "对称" in suggestion_text
        self.assertTrue(has_symmetry_feedback)


if __name__ == "__main__":
    unittest.main()

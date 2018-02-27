import datetime

import ddt
import pytz
from django.test import RequestFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from openedx.core.lib.courses import course_image_url
from student.roles import CourseInstructorRole, CourseStaffRole
from student.tests.factories import UserFactory
from ..utils import serialize_datetime
from ...serializers.course_runs import CourseRunSerializer


@ddt.ddt
class CourseRunSerializerTests(ModuleStoreTestCase):

    def setUp(self):
        super(CourseRunSerializerTests, self).setUp()

        self.start = datetime.datetime.now(pytz.UTC)
        self.end = self.start + datetime.timedelta(days=30)

        self.request = RequestFactory().get('')

    def get_course(self, self_paced, enrollment_start=None, enrollment_end=None):

        if enrollment_start and enrollment_end:
            return CourseFactory(
                start=self.start, end=self.end, self_paced=self_paced, enrollment_start=enrollment_start,
                enrollment_end=enrollment_end
            )
        else:
            return CourseFactory(start=self.start, end=self.end, self_paced=self_paced)

    def get_course_user_roles(self, course):

        instructor = UserFactory()
        CourseInstructorRole(course.id).add_users(instructor)
        staff = UserFactory()
        CourseStaffRole(course.id).add_users(staff)

        return instructor, staff

    def get_expected_data(
        self, course, start, end, enrollment_start, enrollment_end,
        instructor, staff, expected_pacing_type
    ):
        return {
            'id': str(course.id),
            'title': course.display_name,
            'schedule': {
                'start': serialize_datetime(start),
                'end': serialize_datetime(end),
                'enrollment_start': enrollment_start,
                'enrollment_end': enrollment_end,
            },
            'team': [
                {
                    'user': instructor.username,
                    'role': 'instructor',
                },
                {
                    'user': staff.username,
                    'role': 'staff',
                },
            ],
            'images': {
                'card_image': self.request.build_absolute_uri(course_image_url(course)),
            },
            'pacing_type': expected_pacing_type,
        }

    @ddt.data(
        ('instructor_paced', False),
        ('self_paced', True),
    )
    @ddt.unpack
    def test_data_with_enrollment_dates(self, expected_pacing_type, self_paced):

        enrollment_start = self.start - datetime.timedelta(days=7)
        enrollment_end = self.end - datetime.timedelta(days=14)
        course = self.get_course(self_paced, enrollment_start, enrollment_end)
        instructor, staff = self.get_course_user_roles(course)
        serializer = CourseRunSerializer(course, context={'request': self.request})

        expected = self.get_expected_data(
            course, self.start, self.end, serialize_datetime(enrollment_start),
            serialize_datetime(enrollment_end), instructor, staff, expected_pacing_type
        )

        assert serializer.data == expected

    @ddt.data(
        ('instructor_paced', False),
        ('self_paced', True),
    )
    @ddt.unpack
    def test_data_without_enrollment_dates(self, expected_pacing_type, self_paced):

        course = self.get_course(self_paced)
        instructor, staff = self.get_course_user_roles(course)
        serializer = CourseRunSerializer(course, context={'request': self.request})

        expected = self.get_expected_data(
            course, self.start, self.end, None, None, instructor, staff,
            expected_pacing_type
        )

        assert serializer.data == expected

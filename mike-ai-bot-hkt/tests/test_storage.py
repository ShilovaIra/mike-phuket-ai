from storage import AssetStorage
from tests.conftest import S3_BUCKET as BUCKET
from tests.conftest import S3_ENV as ENV

ALL_USERS = "http://acs.amazonaws.com/groups/global/AllUsers"


def test_from_env_without_s3_settings_returns_none():
    assert AssetStorage.from_env({}) is None


def test_upload_stores_public_object_and_returns_cdn_url(s3):
    storage = AssetStorage.from_env(ENV)

    url = storage.upload("partners/7/logo.png", b"png-bytes", "image/png")

    assert url == "https://cdn-test.mikephuketai.com/partners/7/logo.png"
    obj = s3.get_object(Bucket=BUCKET, Key="partners/7/logo.png")
    assert obj["Body"].read() == b"png-bytes"
    assert obj["ContentType"] == "image/png"
    grants = s3.get_object_acl(Bucket=BUCKET, Key="partners/7/logo.png")["Grants"]
    assert {"Grantee": {"Type": "Group", "URI": ALL_USERS}, "Permission": "READ"} in grants


def test_delete_removes_uploaded_object(s3):
    storage = AssetStorage.from_env(ENV)
    storage.upload("cafes/3/front.jpg", b"jpg-bytes", "image/jpeg")

    storage.delete("cafes/3/front.jpg")

    assert s3.list_objects_v2(Bucket=BUCKET).get("KeyCount") == 0


def test_expire_prefix_sets_one_lifecycle_rule_even_when_applied_twice(s3):
    storage = AssetStorage.from_env(ENV)

    storage.expire_prefix("tmp/", days=1)
    storage.expire_prefix("tmp/", days=1)

    rules = s3.get_bucket_lifecycle_configuration(Bucket=BUCKET)["Rules"]
    assert len(rules) == 1
    assert rules[0]["Status"] == "Enabled"
    assert rules[0]["Filter"]["Prefix"] == "tmp/"
    assert rules[0]["Expiration"]["Days"] == 1


def test_public_url_tolerates_trailing_slash_in_base_url():
    storage = AssetStorage.from_env({**ENV, "S3_PUBLIC_BASE_URL": "https://cdn-test.mikephuketai.com/"})

    assert storage.public_url("places/kata.jpg") == "https://cdn-test.mikephuketai.com/places/kata.jpg"

from hashlib import sha256
from pathlib import Path

import pytest

from hiero_did_sdk_python.hcs import HcsFileChunkMessage
from hiero_did_sdk_python.hcs.hcs_file import build_file_from_chunk_messages, get_file_chunk_messages

TEST_FILE_CHUNK_MESSAGES = [
    HcsFileChunkMessage(
        0,
        "data:application/json;base64,KLUv/WBQAZUKACaZPhqAKc0BUmRjIzmfou0kBKXnwyhjwgb0BjQLMDYANgA3AHZCZfosvSPWKWaJ46vzkNVTqXBzQ6UUaIE37sFO7sdLNSUaic8QKYE+Vfw1IYNKT97xHidEEGbzQh60OJ88ocleGk6yjHvKOkUFnYNIy5gsaPEsx3vCEuheok+dCvdkY3IlCjr3dPFcrFSoYmhHAy1OEqpTWUL9kRIN2VsmyRO80LJ0VGnxlbgbG62ETpVw9J4DLYrZuI1LbhglLo9jJLaau1UAAQXWD2mjv9tJNJ+Xk8VsuKHn5toNEWQ0G+OjdpQMWlxeSmJ+qCMu76noEkuzGy1GaNGTJTkhIBCGmKM+abHchNqWJOA4YUgHBFO3P4Iwrrlpl69COfdK6a/dAbtd1YDOdtdIwLFaEDNwidIZx1DjZwJcOdLYcprkFtsCelo3xvARCv5ayWH93ro9",
    )
]

TEST_FILE_LARGE_CHUNK_MESSAGES = [
    HcsFileChunkMessage(
        0,
        "data:application/json;base64,KLUv/WDjMw2FAMpOnAsgQE3SNvCye6PRto/0/2cjcCsZ+a+sRazytkkijg71bAKtALIAsAB3N5SxgyoKrUHrPRWo4gVTGe0w1Q9cvXQvO1uOcKLs8DBTxlkkf2woQzUa4qj8FqjCnA33cZUbDEVyD2Qtvjr5s/M5sQ2qSL8c9WzlGi9rhjyuoUomIZRK2TmroIqvueZRK1eNyquQRx+XLGISyq9L06W2ClZqY7JTX1N5VUOlWwQ5y3tYK2Sr8HPDcAlUoT+uw73kjxsrXLUW56VSRI2s9FmYTjKFNo8XMiYEAWSt4JLafi92iHHaPXH2SDsXW4Iq0G9dNzAlqELhrHFNJw6G0hDPnxczVLGjvkEf6HprXu6qhnsQZDeYjHQGJMoe8kJ2NVDFHi1h0ycqDQlUcZZoS7Ef7mgwRh+sl3COFW0o61mRK0x6VUyHj+jN2TFOQlWMVLEFrdLHTHLmzfnIdQAgAIAAhdoPa0M9f2j1jG7QmrNxo9DPdb9UkvV8jo+6J2RQRW7ilvODJcnNY6mr3AbEzBOGhyL3I8SHbLEXwaRlra7Go+7FfmxY7hICjRiiE09kQj9N0weXG0scQhWZbIjKpIfLnRhqpiu7sehjFTBpGSa1WoVMLynr+mKqh1WmHQJVOE3STaoCOXPRFwwVMTd0sXMUUR9sPSsGN7FMQ6QMmYIq9Jw2dDwKMoMT0GjOiELP/B1ukuZG0AcI41d3S1wqZmwRSWjjJxOa+Kgduiclzh5+6njJRYu6mHzK6M10BAACFHcjxch6wXtXe15CMV1T7EuuAHmCWZOTzzU/Rgte35N5Ot2ujRKIAJv93NhiIwjjyIocX5egjxMm5vctE+JjoiZEk09BGFbs6CzRfTqeJ6jY2tTQRNfqqIim1c5RDFGXsD4iqHLNsaRdkYSOq2hH5U0ZR1K",
    ),
    HcsFileChunkMessage(
        1,
        "7F1xQBbLVdI+zW+cftuA1uXSErCFp55z5PKCK9RFxQErugSowKSHm5L6GUEUxfWBOMBV0TlR6hjDnBIZrqMMMrUIzIiMiKShIkg4jEJAAgcECxcf1g3kHE0AMi2MpaZlKNJOUUad+dUvO8afcgqzVmRfBThR4BYlH2+lk2ImCukG7MZi34OxV9bVLFfou8EEQZJjqgYb6Du6Z2ivleNR/cZAkzms7+JpyScdeB4QyqmBBGMFAPRXb4kyw3n9WCzRBuAeEgtDt4u2jJLhBPAKSOV7d8HW/u3HyfFMkf3xXtmDEClzm26DkbIo4XCe9ouOwMfO5/SSadQJ5HW2FLAqB4YQ7iq/S38yQsD5yRAZb5Mg9gbLT3QTrV5Yw4T18evwU5I8GYZSBsvHaOEZ+tIVrRVYBuaYpRzBqfTESFG7QlYesIowpbcR8xCfP3jK3wsb7K/isNNyQFMP5uo9xxOOgTQ/TK461xV+ActlI6je356FZMiyjwhq+R+LMHNNpw5zhYULV0ZvmUMT2Qms0+mzuaONQUcdBBkP8S51rxMqJYMSnGhbQqxlwCdVFpSqgMcwmt4iPyQRsxKgmbIc9i+2A1Acy5aYRPF6bPjGvC7SwOxmYRDw2cC+H7YPNHSzQ/6bsEwFLxTvjFYOxF+B3KpHmpD0Rxp6e8zd4aooWmuBsKyN/UZ6MnaVJzKxW9ifh5S/oyAigKRkLRcQb82Bn7rkXKQLwRe6GCO5a0TSPCrlcGmGr+v14N51fDs7eBuikxQhoc0Cp1DP7FK81TEuQZjpeffFrqXtqUGIMXfBSmcwqzpaSGnN7EpiDm/kfx+2Nnk8MNcbaXKpzDCMuRQIy6dwFw5icDhSx9GioLoKOQyzVMMxgughEvQ0Qu4VR/JVdztsCpXMNUTd63AvsEWbjmxa8sw1+f+rhUkrOgx5z5ZjXSxx6z3Rr03fLdeVmTg2dqA8",
    ),
    HcsFileChunkMessage(
        2,
        "TnN09HYn/dNWGlmiqm+WECdmicZ/T1UbNJUwvqasnaNX6fEcg0NsK5brQOIa7PzCz0URcZwALmSGaDa05kTmSOgxUs6X7Vv3HkwhqEsJZM00UzbSe6g2WjnNJo2KM1AhJX1EOi7Rx7Ode2EzKiC6XqnWOAbm2VjIu9AcTweJQxAhhNxp/maoqqjWz16MIEzIxiE8a+j/ak3jBCg5IMHs0PsHRGJ3H3l7tT1yV3SuAOvxvmtaopvRPtT9pmUbR2WdL0702nlOESeOq+g7hrA3gBo6B0dJ5hrMkQPuBZCSsr8iP3l/gJ8FcUkEjK3/Onrg2oR7yLiczOJlKw8HA0LWwQoJCjwz0srpHApPuXSOe8vqbYkrO8zNauE8zoT2e9qenhSDM8PNJ8NlxoGvLJLJ1/xn4FuaNboyZGHYOyX/BDL4uKWRHWOfH3wVXseAsjwVNX9PJM5LF5SmNOI9oV7urXqbfZsRM6NlTSXUo7wIGqSJesGUtd2do8yPpyYkH3IzdXTqslVFphkkBg7538qVGJ51Ql1UzMMI/Q3qyjVU/sDRnTcfJC5rMGnMQABcOisVfje+aLRyqTflZa+2OPsdZYmfTyGLdZXAAyfqDxWYh5xAp9qFhNVZ2kXOD9/KPtjlp4kx0wtk+7f5eQ41cjk5u1aGpV1aTfDUMXi4ViXYdAKOLnimG3GqpeTo6oHuUjuMr4nI46wL+cIqnExbEKUltoyBiUXQTP8WtEtBYjhs/VKavhP5QvszK3UNAdF1+/cQ4RhsArXxgfSE0DDdP02DDt8/liKe6+OGv5C4ShKJFgNYmm6yUnoxspUX2IbvOZaBbEAZEpOcX7NiFyFBNS5Y+ZUI5rWQAovK/08MRGmwiXC4EMADkRKkml5v2TTN2rSo8TXA68JtA/D6QYtbLWEGwjlV33EvtV9g9Igef5y551JOdHrZrPA5vEulG4yj1hB6",
    ),
    HcsFileChunkMessage(
        3,
        "yPKovS5fQpDEYmzL+uGsU5FIRdPrHnPgCATDoNUrbgLZhT8MtCBa7E0w6qMSOeTFjKG3eUwt/J+fjTgebUrvOP4h18B3OQzPaFwsbIrc2OYXMgdgFytsW5C82NMF5UZk2dtBRaQpHgom7rMLbOzwmpxgOnLx1cTOKSh/8qLp599cjnNDsHACPuqIHYfNl7t1qInYgXCSExIugG/Q44nCiZOjdoHejpwdccvRJuzRd5rJsdL3JfMDk1yDBGZE3lBQTEhpd/zY6PSL93zRuuIyKdBFco0K0W2wQ0IPVaz/izSnwNhiKc47UP3k++47qKEdBUni5+2y6VJ+gqCdq9tVlbyNxYgHs+H4objl6ycLB4gkXyDsdySF9Ig0FvVQwaqkJ//GK+ZnS9Ia4sXAhjHYigR7Or022kwGoekWInDWg4oj2LnIMV6jzl4DGT9B5SkD/R5bLToQ0RfblahONL5VAFUXzuJvaSV5QDQzQbVLF5fNkT/INKqswNQec5QdSv4PzgjdcNQt3SRCNrRz6qsDY5rqFxSwz1m4g4znFURqJYE1foxzfhGh33mOj+AYHB/mOz5ufS0KC1jvzk0GBaz69Q+m7dgAMPJfYESTV1KrfWWAeerw82X5+XfDserL8k4FZmXjrLFHRgPtObYFo53imFWeld25lKbuzIYZPmQWOS6wPrNQsNaKfnVO1kngMlRitKDar+bjZ98DBrLTODCXxMtknq5U1r45AvrZyXijRbHovC9bigGFs1RR54UHQ8RwRj9ZIcp3oIwORukimyLZIojbAjsYsWNtpr62X5SB9FY0/RVG4ZdowmLN5cD4VcoCt5gaedY2qZ/elX0WDQXYYoEhJIWUPOYA3SR/gqM3TNBrAONOSaVmwi0jt0DAPwqAqjEpmKRlyXcD1eaVk34cwAZ1mCqn+qNiXZQ4IRQWn3BeqFA+KQzCWBm5JFxyvM9R",
    ),
    HcsFileChunkMessage(
        4,
        "jqlnzk50gMgq/Z2lXykiBqL/4xEtWvbR/s3AqJSxLpJ2W/2Q9smXFel+7CtTNZi0UXTLsQIJRGk/TZuK5dqZY5XVjgbjSz/1pAH0pST96MsLJ9Va3Z4yJt5EPy3KooWpmahlLnW74tV8uKGQIWf8hz9OQJXgPeoh5R0VYZRGZADBGJvQkCEiN1Mz4HddQGI6w6rrjh6H3UNWhFPs34rZMmHwIVQ1NDT0Y6sIE8w41B0bfKHSL2j1IKDGB7v20qoLdvBCsvrB2T1BT8lAZnjL2eLWN2MhDv5NXM0GguRGgWFS7eXmTApaSqRmixeT4bs11SqtKmTP623lnIdjDm0GZ+ce+V4DDJ6yxVd/pYh3PgbJ03zDjOcX2S02R2/ap6SfRrJKzAHCqfkFijKlRiTG+GIciZQ0ZibPF0OUU6AWMwyTSwSIytVwbPMHgyMwB5ZpAI8iN9m4a72mtW8/nbcY+oybly50RdDzOkijCpukdmmB7Wnw4it2wbqXKZDYj3fp1BXCADjymjV5ueKso8gz7vfESrpMQm3JvLodSdNt8ouvcRt+THqO8nzxk6RGdBOEZBMfm1lnwTD/FpljgtssOTlOFvxnVv9nG++Up4YE+UlTEE/gBBld4WvIB/zMiZON7VErDLUKczavhvFhgt7ix91JeLt+vtPUapFtVjt7YeoiQj9dZIw99fCMt32OorP6QnYH6ePGFVXEiDnwNYyWicJnXFPfK4DMMuAnpX7tSb2c4SbewuiZ3rzdkhCXHOJlYm/nYWBL/tP5spOK5E473MRMd3dmw1pHoB3WVVVPLu26Vqf3ILxM9IRpi+cFzCPOZp1kZ5USRXUERbjpLb5chLvFO1Oo+4ssKDNmCs2PZ0gXckwXFQ5qy7Uxl5Z+cSkr2pVale3hW4KvVSs6NBJJAl+AbXgJOYcXHCI3ufwqOPgJCAiK4Gu9bWHc7lXHegEC",
    ),
    HcsFileChunkMessage(
        5,
        "+mgScYzGRilyfhWEzfH/BcuD0B//g1zkVk9god4yyEj7b7pqjlLsXtt6xlXkR4LSOs8x5hzs98iuWtfXvWWkSAdPJAGJctbCIFUv8Thuk/uc7J/x3293BZBQ7RRhB4SLBknv5P3j4bDY3PxrdUKyue4vo//rws/bMD1GiY6JQFXcAuPUspvaYlchM2aa1oAGAd06yPiRjzVQRd3lZRbxKsSGi29EeYiMHePNZN+6sw37n6TvpNSpL+skw853fda0/raCANG7ilA79N9k4b3q8B2rhPaBosr2vURYqIU2hgC8rzqrQH9EmwEd5JL0LWWCJF43Zohtn/Nk2skCV1bfYoNWruf9kx2aWIiFFswc0JYxjVnZjnH2aSMbXk+qcdZQtbOchTsZJPrO3Ii02IXcstJicHA/Z97+LZA9onx0tBBQKSEhHqolCPyRkRElqQllGqlspVFojfikit/2Dzf69idwdjFVsQgX1kKTS0v2JozxwAFOyaTC0uAVtEVtdcIoktqgTtRzfbra++XS6KmtqPm+gYoHHfQ6405K+wBVXmNxjgPnZt3bT7dN2s8YDvEzh6ZGtEQctjaMOFMSXFvBiYV9lbJzcDWRmjmK0f1taULbzEeUH77GnzxJlwJXzofQatDwZSqJS42vvQ9/ZHodiUpGSt3xe5YHDyn0jxTtjpnU3hPEA5SOEwvOEd6rEYCuBHWB0yiT9c2fjTfGonSXNmj2wEUUriumpOfSUyx/uAMTcosp2CHTUUQUd4NafwZXmfQURHH4BMSc+FJt6qNfrvMDrVF+FoigVOV3aQpvwKAHzMTSJ8WBlPzILs85tBHwmn3eZSBPRmudgxnX70kGs4Z1xHEJAkYVXF/XEwhB59lavyFZjBE0zoJZf56DApbtx9GznbIxgg8GS3+u+jzF2BQ==",
    ),
]


class TestHcsFileUtils:
    @pytest.mark.parametrize(
        "test_file_path, expected_chunks_count",
        [("./tests/test_data/test_file.txt", 1), ("./tests/test_data/test_file_large.txt", 6)],
    )
    def test_get_chunk_message(self, test_file_path: str, expected_chunks_count: int):
        file_payload = Path(test_file_path).read_bytes()

        chunk_messages = get_file_chunk_messages(file_payload)

        assert len(chunk_messages) == expected_chunks_count

        for message in chunk_messages:
            assert isinstance(message, HcsFileChunkMessage)
            assert len(message.content.encode()) <= HcsFileChunkMessage.MAX_CHUNK_CONTENT_SIZE_IN_BYTES

    @pytest.mark.parametrize(
        "chunk_messages, expected_hash",
        [
            (TEST_FILE_CHUNK_MESSAGES, "ea4d17b8c0cf44c215ade6b4ad36832672ea3188b1dad12b68c2472dfbcdeff1"),
            (TEST_FILE_LARGE_CHUNK_MESSAGES, "dce9e97491cb7bbaeb6f1af9c236a62f5b6f3f4c07952b5431daa52ec58fbc0b"),
        ],
    )
    def test_build_file_from_chunk_messages(self, chunk_messages: list[HcsFileChunkMessage], expected_hash: str):
        file_payload = build_file_from_chunk_messages(chunk_messages)
        assert sha256(file_payload).hexdigest() == expected_hash

    def test_build_file_from_chunk_messages_throws_on_invalid_data(self):
        invalid_chunk_messages = [HcsFileChunkMessage(0, "invalid_chunk_data")]
        with pytest.raises(
            Exception,
            match="Error on building HCS-1 file payload from chunk messages: error determining content size from frame header",
        ):
            build_file_from_chunk_messages(invalid_chunk_messages)

        invalid_chunk_messages = [
            HcsFileChunkMessage(0, "data:application/json;base64,KLUv/WBQAZUKACaZPhqAKc0BUmRjIzmfo!!")
        ]
        with pytest.raises(
            Exception, match="Error on building HCS-1 file payload from chunk messages: Invalid base64-encoded string"
        ):
            build_file_from_chunk_messages(invalid_chunk_messages)

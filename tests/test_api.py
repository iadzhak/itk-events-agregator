import pytest
from fastapi import status


@pytest.mark.unit
@pytest.mark.asyncio
class TestHealth:
    async def test_health_success(self, test_client):
        response = await test_client.get('api/health')
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {'status': 'ok'}

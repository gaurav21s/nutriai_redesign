"""Calculator endpoints."""

from fastapi import APIRouter, Depends, Query

from app.core.security import AuthContext, get_auth_context
from app.dependencies import default_rate_limit, get_calculator_service
from app.schemas.calculators import (
    BMIRequest,
    BMIResponse,
    CaloriesRequest,
    CaloriesResponse,
    CalculationHistoryResponse,
)
from app.services.calculator_service import CalculatorService

router = APIRouter(prefix="/calculators", tags=["Calculators"])


@router.post(
    "/bmi",
    response_model=BMIResponse,
    summary="Calculate BMI",
    description="Computes BMI and returns health category.",
    dependencies=[Depends(default_rate_limit)],
)
async def calculate_bmi(
    payload: BMIRequest,
    auth: AuthContext = Depends(get_auth_context),
    service: CalculatorService = Depends(get_calculator_service),
) -> BMIResponse:
    return await service.calculate_bmi(auth.clerk_user_id, payload)


@router.post(
    "/calories",
    response_model=CaloriesResponse,
    summary="Calculate maintenance calories",
    description="Computes BMR and daily maintenance calories based on activity multiplier.",
    dependencies=[Depends(default_rate_limit)],
)
async def calculate_calories(
    payload: CaloriesRequest,
    auth: AuthContext = Depends(get_auth_context),
    service: CalculatorService = Depends(get_calculator_service),
) -> CaloriesResponse:
    return await service.calculate_calories(auth.clerk_user_id, payload)


@router.get(
    "/history",
    response_model=CalculationHistoryResponse,
    summary="List calculator history",
    description="Returns BMI and calorie calculation history for current user.",
    dependencies=[Depends(default_rate_limit)],
)
async def get_calculation_history(
    limit: int = Query(default=20, ge=1, le=100),
    auth: AuthContext = Depends(get_auth_context),
    service: CalculatorService = Depends(get_calculator_service),
) -> CalculationHistoryResponse:
    items = await service.get_history(auth.clerk_user_id, limit)
    return CalculationHistoryResponse(items=items)

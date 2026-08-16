from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models import Goal, User
from app.repositories.goal_repository import GoalRepository
from app.schemas.goal import GoalCreate, GoalPatch, GoalPublic, GoalUpdate
from app.utils.nutrition import remaining
from app.utils.pagination import PaginatedResponse, paginated


class GoalService:
    def __init__(self, db: Session, user: User) -> None:
        self.db = db
        self.user = user
        self.goals = GoalRepository(db)

    def list_goals(self, page: int, page_size: int) -> PaginatedResponse[GoalPublic]:
        offset = (page - 1) * page_size
        items, total = self.goals.list_for_user(self.user.id, offset=offset, limit=page_size)
        return paginated(
            [self._to_public(goal) for goal in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def create(self, payload: GoalCreate) -> GoalPublic:
        if self.goals.get_for_user(self.user.id) is not None:
            raise AppError("GOAL_EXISTS", "Goals are already set for this account", 409)
        try:
            goal = self.goals.create(self.user.id, **payload.model_dump())
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError("GOAL_EXISTS", "Goals are already set for this account", 409) from exc
        return self._to_public(goal)

    def replace(self, payload: GoalUpdate) -> GoalPublic:
        goal = self._require_goal()
        for field, value in payload.model_dump().items():
            setattr(goal, field, value)
        self.db.commit()
        self.db.refresh(goal)
        return self._to_public(goal)

    def patch(self, payload: GoalPatch) -> GoalPublic:
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise AppError("VALIDATION_ERROR", "At least one field is required", 422)
        goal = self._require_goal()
        for field, value in updates.items():
            setattr(goal, field, value)
        self.db.commit()
        self.db.refresh(goal)
        return self._to_public(goal)

    def delete(self) -> None:
        goal = self._require_goal()
        self.goals.delete(goal)
        self.db.commit()

    def _require_goal(self) -> Goal:
        goal = self.goals.get_for_user(self.user.id)
        if goal is None:
            raise AppError("RESOURCE_NOT_FOUND", "Goals have not been set", 404)
        return goal

    def _to_public(self, goal: Goal) -> GoalPublic:
        day = datetime.now(timezone.utc).date()
        actual = self.goals.todays_macros(self.user.id, day)
        return GoalPublic(
            id=goal.id,
            user_id=goal.user_id,
            daily_calorie_target=goal.daily_calorie_target,
            protein_target=goal.protein_target,
            carb_target=goal.carb_target,
            fat_target=goal.fat_target,
            weight_goal=goal.weight_goal,
            calories_actual=actual.calories,
            protein_actual=actual.protein,
            carb_actual=actual.carbohydrates,
            fat_actual=actual.fat,
            calories_remaining=remaining(goal.daily_calorie_target, actual.calories),
            protein_remaining=remaining(goal.protein_target, actual.protein),
            carb_remaining=remaining(goal.carb_target, actual.carbohydrates),
            fat_remaining=remaining(goal.fat_target, actual.fat),
            progress_date=day,
            created_at=goal.created_at,
            updated_at=goal.updated_at,
        )

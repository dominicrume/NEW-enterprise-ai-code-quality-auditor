import { Router, type IRouter } from "express";
import { eq } from "drizzle-orm";
import { db, coursesTable, lessonsTable } from "@workspace/db";
import { requireAuth } from "../middlewares/auth";
import { GetCourseParams } from "@workspace/api-zod";

const router: IRouter = Router();

router.get("/courses", requireAuth, async (req, res): Promise<void> => {
  const courses = await db.select().from(coursesTable).orderBy(coursesTable.id);

  const lessonCounts = await db.select().from(lessonsTable);
  const countMap = new Map<number, number>();
  for (const l of lessonCounts) {
    countMap.set(l.courseId, (countMap.get(l.courseId) ?? 0) + 1);
  }

  const result = courses.map((c) => ({
    id: c.id,
    title: c.title,
    description: c.description,
    category: c.category,
    lessonCount: countMap.get(c.id) ?? 0,
  }));

  res.json(result);
});

router.get("/courses/:id", requireAuth, async (req, res): Promise<void> => {
  const params = GetCourseParams.safeParse(req.params);
  if (!params.success) {
    res.status(400).json({ error: params.error.message });
    return;
  }

  const [course] = await db.select().from(coursesTable).where(eq(coursesTable.id, params.data.id));
  if (!course) {
    res.status(404).json({ error: "Course not found" });
    return;
  }

  const lessons = await db
    .select()
    .from(lessonsTable)
    .where(eq(lessonsTable.courseId, course.id))
    .orderBy(lessonsTable.orderIndex);

  res.json({
    id: course.id,
    title: course.title,
    description: course.description,
    category: course.category,
    lessonCount: lessons.length,
    lessons: lessons.map((l) => ({
      id: l.id,
      title: l.title,
      content: l.content,
      orderIndex: l.orderIndex,
    })),
  });
});

export default router;

import React, { useEffect } from "react";
import { useLocation, Link } from "wouter";
import { useListCourses, getListCoursesQueryKey } from "@workspace/api-client-react";
import { Layout } from "@/components/layout";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { BookOpen, Layers } from "lucide-react";

export default function Courses() {
  const [, setLocation] = useLocation();

  useEffect(() => {
    if (!localStorage.getItem("auth_token")) {
      setLocation("/login");
    }
  }, [setLocation]);

  const { data: courses, isLoading, error } = useListCourses({
    query: {
      queryKey: getListCoursesQueryKey(),
      enabled: !!localStorage.getItem("auth_token")
    }
  });

  return (
    <Layout>
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-foreground mb-2">Course Catalog</h1>
        <p className="text-muted-foreground">Explore available training programs and expand your skills.</p>
      </div>

      {error ? (
        <div className="p-6 bg-destructive/10 text-destructive rounded-lg border border-destructive/20" data-testid="text-error">
          Failed to load courses. Please try again later.
        </div>
      ) : isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i} className="overflow-hidden border-border/50">
              <CardHeader className="pb-4">
                <Skeleton className="h-6 w-3/4 mb-2" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-2/3" />
              </CardHeader>
              <CardContent>
                <div className="flex gap-2">
                  <Skeleton className="h-5 w-20 rounded-full" />
                  <Skeleton className="h-5 w-24 rounded-full" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {courses?.map((course) => (
            <Link key={course.id} href={`/courses/${course.id}`} className="group hover-elevate transition-all duration-200" data-testid={`link-course-${course.id}`}>
              <Card className="h-full flex flex-col border-border/50 shadow-sm group-hover:shadow-md group-hover:border-primary/20 transition-all">
                <CardHeader className="pb-4">
                  <div className="flex justify-between items-start mb-2">
                    <Badge variant="secondary" className="bg-secondary/50 text-secondary-foreground" data-testid={`badge-category-${course.id}`}>
                      {course.category}
                    </Badge>
                  </div>
                  <CardTitle className="text-xl group-hover:text-primary transition-colors line-clamp-2" data-testid={`text-course-title-${course.id}`}>
                    {course.title}
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex-1">
                  <CardDescription className="text-base line-clamp-3" data-testid={`text-course-desc-${course.id}`}>
                    {course.description}
                  </CardDescription>
                </CardContent>
                <CardFooter className="pt-4 pb-6 border-t border-border/40 text-sm text-muted-foreground flex items-center gap-2">
                  <Layers className="w-4 h-4" />
                  <span data-testid={`text-course-lessons-${course.id}`}>{course.lessonCount} {course.lessonCount === 1 ? 'lesson' : 'lessons'}</span>
                </CardFooter>
              </Card>
            </Link>
          ))}
          {courses?.length === 0 && (
            <div className="col-span-full py-12 text-center text-muted-foreground border-2 border-dashed border-border rounded-xl">
              <BookOpen className="w-12 h-12 mx-auto mb-4 opacity-20" />
              <p className="text-lg font-medium">No courses available</p>
              <p className="text-sm mt-1">Check back later for new content.</p>
            </div>
          )}
        </div>
      )}
    </Layout>
  );
}

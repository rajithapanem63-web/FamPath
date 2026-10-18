'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { useToast } from '@/hooks/use-toast';
import { Progress } from '@/components/ui/progress';
import { post } from '@/lib/api';
import { useWorkspaceStore } from '@/stores/workspaceStore';

type Weight = 'LOW' | 'MEDIUM' | 'HIGH';

interface DimensionData {
  dimension: string;
  label: string;
  description: string;
  weight: Weight;
  options: string[];
  selectedOptions: string[];
}

const DIMENSIONS = [
  {
    dimension: 'branch_preference',
    label: 'Branch Preference',
    description: 'Which engineering branches interest you?',
    options: ['CSE', 'IT', 'ECE', 'EEE', 'Mechanical', 'Civil', 'Chemical'],
  },
  {
    dimension: 'location_preference',
    label: 'Location Preference',
    description: 'Where would you prefer to study?',
    options: ['Hyderabad', 'Vijayawada', 'Visakhapatnam', 'Warangal', 'Tirupati', 'Any'],
  },
  {
    dimension: 'college_type_preference',
    label: 'College Type',
    description: 'What type of college do you prefer?',
    options: ['Government', 'Private Autonomous', 'Private Affiliated', 'Deemed University'],
  },
  {
    dimension: 'budget_constraint',
    label: 'Budget',
    description: 'What is your budget range for 4 years?',
    options: ['Under 2L', '2-5L', '5-10L', '10-20L', 'Above 20L'],
  },
  {
    dimension: 'placement_importance',
    label: 'Placement Priority',
    description: 'How important are placements to you?',
    options: ['Very Important', 'Important', 'Moderate', 'Not a priority'],
  },
  {
    dimension: 'campus_facilities',
    label: 'Campus Facilities',
    description: 'What facilities matter most?',
    options: ['Hostel', 'Library', 'Labs', 'Sports', 'Transport', 'Wi-Fi'],
  },
  {
    dimension: 'reputation_ranking',
    label: 'Reputation/Ranking',
    description: 'How important is college reputation?',
    options: ['Very Important', 'Important', 'Moderate', 'Not a priority'],
  },
  {
    dimension: 'career_goal',
    label: 'Career Goal',
    description: 'What is your primary career goal?',
    options: ['Software Job', 'Core Engineering Job', 'Higher Studies (MS)', 'Research', 'Entrepreneurship', 'Government Job'],
  },
];

export default function PreferencesPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { workspace } = useWorkspaceStore();
  const [loading, setLoading] = useState(false);
  
  const [responses, setResponses] = useState<DimensionData[]>(
    DIMENSIONS.map(d => ({
      ...d,
      weight: 'MEDIUM' as Weight,
      selectedOptions: [],
    }))
  );

  const completed = responses.filter(r => r.selectedOptions.length > 0).length;
  const progress = (completed / DIMENSIONS.length) * 100;

  const handleWeightChange = (index: number, weight: Weight) => {
    const newResponses = [...responses];
    newResponses[index]!.weight = weight;
    setResponses(newResponses);
  };

  const handleOptionToggle = (dimensionIndex: number, option: string) => {
    const newResponses = [...responses];
    const current = newResponses[dimensionIndex]!.selectedOptions;
    
    if (current.includes(option)) {
      newResponses[dimensionIndex]!.selectedOptions = current.filter(o => o !== option);
    } else {
      newResponses[dimensionIndex]!.selectedOptions = [...current, option];
    }
    
    setResponses(newResponses);
  };

  const handleSubmit = async () => {
    // Validate: at least one option per dimension
    const incomplete = responses.filter(r => r.selectedOptions.length === 0);
    if (incomplete.length > 0) {
      toast({
        title: 'Incomplete questionnaire',
        description: `Please select at least one option for: ${incomplete.map(r => r.label).join(', ')}`,
        variant: 'destructive',
      });
      return;
    }

    if (!workspace?.id) {
      toast({
        title: 'No workspace selected',
        description: 'Please select a workspace first.',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);
    try {
      await post('/preferences', {
        workspace_id: workspace.id,
        responses: responses.map(r => ({
          dimension: r.dimension,
          weight: r.weight,
          selected_options: r.selectedOptions,
        })),
      });

      toast({
        title: 'Preferences saved!',
        description: 'Your questionnaire has been submitted successfully.',
      });
      
      // Redirect to dashboard
      router.push('/en/dashboard');
    } catch (error: any) {
      console.error('Failed to submit preferences:', error);
      const errorMsg = error?.response?.data?.message || error?.response?.data?.detail || 'Failed to submit preferences. Please try again.';
      toast({
        title: 'Error',
        description: errorMsg,
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Preference Questionnaire</h1>
        <p className="text-muted-foreground mb-4">
          Help us understand your priorities for college selection.
        </p>
        
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Progress: {completed}/8 dimensions</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>
      </div>

      <div className="space-y-6">
        {responses.map((dim, index) => (
          <Card key={dim.dimension} className={dim.selectedOptions.length > 0 ? 'border-green-500' : ''}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {dim.label}
                {dim.selectedOptions.length > 0 && (
                  <span className="text-sm text-green-600">✓</span>
                )}
              </CardTitle>
              <CardDescription>{dim.description}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Weight Selector */}
              <div>
                <Label className="mb-2 block">How important is this?</Label>
                <RadioGroup
                  value={dim.weight}
                  onValueChange={(value) => handleWeightChange(index, value as Weight)}
                  className="flex gap-4"
                >
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="LOW" id={`${dim.dimension}-low`} />
                    <Label htmlFor={`${dim.dimension}-low`} className="cursor-pointer">
                      Low
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="MEDIUM" id={`${dim.dimension}-med`} />
                    <Label htmlFor={`${dim.dimension}-med`} className="cursor-pointer">
                      Medium
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="HIGH" id={`${dim.dimension}-high`} />
                    <Label htmlFor={`${dim.dimension}-high`} className="cursor-pointer">
                      High
                    </Label>
                  </div>
                </RadioGroup>
              </div>

              {/* Options */}
              <div>
                <Label className="mb-2 block">Select your preferences:</Label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {dim.options.map((option) => (
                    <div key={option} className="flex items-center space-x-2">
                      <Checkbox
                        id={`${dim.dimension}-${option}`}
                        checked={dim.selectedOptions.includes(option)}
                        onCheckedChange={() => handleOptionToggle(index, option)}
                      />
                      <Label
                        htmlFor={`${dim.dimension}-${option}`}
                        className="cursor-pointer text-sm"
                      >
                        {option}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-8 flex justify-end gap-4">
        <Button variant="outline" onClick={() => router.back()}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          disabled={loading || completed < 8}
          size="lg"
        >
          {loading ? 'Submitting...' : 'Submit Preferences'}
        </Button>
      </div>
    </div>
  );
}